"""
Write a hospital `SimResult` into the real cymed tables for one demo tenant.

    ED visits        -> EmergencyVisit / EmergencyTriage / EmergencyDisposition
    clinic visits    -> Appointment (+participant) / Encounter (+participant)
    admissions       -> Encounter / Admission / HospitalStay / ICUStay / BedAssignment
    orders           -> Order / OrderItem / OrderResult

The only simulation-owned row is `SimulationRun`. All writes run inside
`tenant_context(tid)` so the per-tenant field encryption on PHI columns works.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, time

from django.db import transaction
from django.utils import timezone

from platform.common.tenant_context import tenant_context

from .engine import SimResult
from .models import SimulationRun
from .scenarios import hospital as H


def _tid_uuid(v):
    return v if isinstance(v, uuid.UUID) else uuid.UUID(str(v))


class HospitalSeeder:
    def __init__(self, result: SimResult, *, slug: str, tenant_name: str,
                 run: SimulationRun | None = None, stdout=None):
        self.r = result
        self.slug = slug
        self.tenant_name = tenant_name
        self.run = run
        self.tag = run.tag if run is not None else "SIM:pending"
        self.counts: dict[str, int] = defaultdict(int)
        self._out = stdout
        self.tenant_id = None
        self.org = None
        self.facility = None
        self.clinic_facility: dict[str, object] = {}
        self.beds_by_ward: dict[str, list] = {}
        self.provider_rows: dict[int, object] = {}
        self.patient_rows: dict[int, object] = {}
        self._admission_type = None
        self._admission_reason = None

    def log(self, m):
        if self._out:
            self._out.write(m)

    # ------------------------------------------------------------------

    def wipe(self):
        from platform.tenant.models import Tenant
        t = Tenant.objects.filter(slug=self.slug).first()
        if not t:
            return
        tid = t.id
        from products.cymed.core.orders.models import Order, OrderItem, OrderResult
        from products.cymed.core.encounters.models import Encounter, EncounterParticipant
        from products.cymed.core.scheduling.models import Appointment, AppointmentParticipant
        from products.cymed.core.patients.models import Patient
        from products.cymed.core.providers.models import Provider, ProviderSpecialty
        from products.cymed.hospital.adt.models import Admission
        from products.cymed.hospital.inpatient.models import HospitalStay
        from products.cymed.hospital.icu.models import ICUStay
        from products.cymed.hospital.bed_management.models import BedAssignment
        from products.cymed.hospital.emergency.models import (
            EmergencyVisit, EmergencyTriage, EmergencyDisposition)

        with transaction.atomic():
            for M in (OrderResult, OrderItem, Order, EncounterParticipant,
                      AppointmentParticipant, Appointment, BedAssignment, ICUStay,
                      HospitalStay, Admission, EmergencyDisposition, EmergencyTriage,
                      EmergencyVisit, Encounter, ProviderSpecialty, Provider, Patient):
                M.objects.filter(tenant_id=tid).delete()
            SimulationRun.objects.filter(tenant_id=tid).exclude(pk=self.run.pk).delete()
        self.log(f"  wiped prior clinical data for tenant '{self.slug}'")

    # ------------------------------------------------------------------

    def set_run(self, run: SimulationRun):
        self.run = run
        self.tag = run.tag

    def ensure_tenant(self):
        """Create/resolve the demo tenant and return its id — callable before a
        SimulationRun exists (SimulationRun is tenant-scoped)."""
        if self.tenant_id is None:
            self._seed_tenant()
        return self.tenant_id

    def seed(self) -> dict:
        self.ensure_tenant()
        with tenant_context(self.tenant_id):
            self._seed_facilities()
            self._seed_providers()
            self._seed_patients()
            self._seed_ed()
            self._seed_clinics()
            self._seed_inpatient()
        self.run.record_counts = dict(self.counts)
        return dict(self.counts)

    # ------------------------------------------------------------------

    def _seed_tenant(self):
        from platform.tenant.models import Tenant, TenantStatus, TenantType
        tenant, _ = Tenant.objects.update_or_create(
            slug=self.slug,
            defaults={
                "name": self.tenant_name, "display_name": self.tenant_name,
                "tenant_type": TenantType.DEDICATED, "status": TenantStatus.ACTIVE,
                "country_code": H.COUNTRY, "timezone": H.TIMEZONE, "locale": "en",
                "activated_at": timezone.now(),
                "metadata": {"city": H.CITY, "demo": True, "simulation": self.r.scenario},
            },
        )
        self.tenant_id = tenant.id
        if self.run is not None and not self.run.tenant_id:
            self.run.tenant_id = tenant.id
            self.run.save(update_fields=["tenant_id"])

    def _seed_facilities(self):
        tid = self.tenant_id
        from products.cymed.core.organizations.models import Organization, OrganizationType
        from products.cymed.core.facilities.models import (
            Facility, Building, Department, Ward, Room, Bed)

        self.org, _ = Organization.objects.get_or_create(
            tenant_id=tid, name="Cymed Health Network",
            defaults={"organization_type": OrganizationType.choices[0][0]},
        )
        self.facility, _ = Facility.objects.get_or_create(
            tenant_id=tid, code=f"{H.HOSPITAL['code']}-{self.slug[:6]}",
            defaults={"organization": self.org, "name": H.HOSPITAL["name"]},
        )
        dept, _ = Department.objects.get_or_create(
            tenant_id=tid, facility=self.facility, code="INPT", defaults={"name": "Inpatient Services"})
        for wcode, (wname, rtype, nbeds) in H.WARDS.items():
            ward, _ = Ward.objects.get_or_create(
                tenant_id=tid, department=dept, name=wname, defaults={"code": wcode})
            room, _ = Room.objects.get_or_create(
                tenant_id=tid, ward=ward, room_number=f"{wcode}-01",
                defaults={"room_type": rtype})
            beds = []
            for b in range(nbeds):
                bed, _ = Bed.objects.get_or_create(
                    tenant_id=tid, room=room, bed_number=f"{wcode}-{b + 1:02d}",
                    defaults={"status": "available"})
                beds.append(bed)
            self.beds_by_ward[wcode] = beds

        for ccode, (cname, spec, rooms, slots) in H.CLINICS.items():
            fac, _ = Facility.objects.get_or_create(
                tenant_id=tid, code=f"{ccode}-{self.slug[:6]}",
                defaults={"organization": self.org, "name": cname})
            self.clinic_facility[ccode] = fac
        self.counts["facilities"] = Facility.objects.filter(tenant_id=tid).count()
        self.counts["beds"] = Bed.objects.filter(tenant_id=tid).count()
        self.log(f"  facilities: hospital + {len(H.CLINICS)} clinics, "
                 f"{self.counts['beds']} beds")

    def _seed_providers(self):
        tid = self.tenant_id
        from products.cymed.core.providers.models import Provider, ProviderSpecialty, ProviderType
        pt_map = {"physician": ProviderType.PHYSICIAN, "nurse": ProviderType.NURSE}
        for pr in self.r.providers:
            prov = Provider.objects.create(
                tenant_id=tid, user_id=uuid.uuid4(), first_name=pr.first, last_name=pr.last,
                provider_type=pt_map.get(pr.ptype, ProviderType.PHYSICIAN),
                npi=f"{pr.npi}-{self.slug[:4]}", is_active=True)
            self.provider_rows[pr.ref] = prov
            spec_disp = H.SPECIALTIES.get(pr.specialty, (pr.specialty,))[0]
            ProviderSpecialty.objects.create(
                tenant_id=tid, provider=prov, specialty_code=pr.specialty.upper(),
                specialty_display=spec_disp)
        self.counts["providers"] = len(self.provider_rows)
        self.log(f"  providers: {self.counts['providers']}")

    def _seed_patients(self):
        tid = self.tenant_id
        from products.cymed.core.patients.models import Patient
        used_refs = (
            {v.patient_ref for v in self.r.ed_visits}
            | {v.patient_ref for v in self.r.clinic_visits}
            | {s.patient_ref for s in self.r.stays}
        )
        for pr in self.r.patients:
            if pr.ref not in used_refs:
                continue
            p = Patient.objects.create(
                tenant_id=tid, first_name=pr.first, last_name=pr.last, dob=pr.dob,
                gender=pr.gender, mrn=f"{pr.mrn}-{self.slug[:3]}", national_id=pr.national_id)
            self.patient_rows[pr.ref] = p
        self.counts["patients"] = len(self.patient_rows)
        self.log(f"  patients: {self.counts['patients']}")

    # ------------------------------------------------------------------

    def _admission_refs(self):
        if self._admission_type is None:
            from products.cymed.hospital.adt.models import AdmissionType, AdmissionReason
            self._admission_type, _ = AdmissionType.objects.get_or_create(
                code=f"SIM-URGENT-{self.slug[:4]}",
                defaults={"tenant_id": self.tenant_id, "name": "Urgent admission"})
            self._admission_reason, _ = AdmissionReason.objects.get_or_create(
                code=f"SIM-CLIN-{self.slug[:4]}",
                defaults={"tenant_id": self.tenant_id, "name": "Clinical deterioration"})
        return self._admission_type, self._admission_reason

    def _backdate(self, model, pk, **fields):
        model.objects.filter(pk=pk).update(**fields)

    def _make_encounter(self, patient, etype, status, start, end, facility):
        from products.cymed.core.encounters.models import Encounter
        return Encounter.objects.create(
            tenant_id=self.tenant_id, patient=patient, encounter_type=etype, status=status,
            start_time=start, end_time=end, organization=self.org, facility=facility)

    def _write_orders(self, patient, encounter, orders):
        if not orders:
            return
        from products.cymed.core.orders.models import (
            Order, OrderItem, OrderResult, OrderType, OrderPriority, OrderStatus)
        kind_map = {"lab": OrderType.LABORATORY, "imaging": OrderType.IMAGING,
                    "medication": OrderType.MEDICATION}
        for o in orders:
            order = Order.objects.create(
                tenant_id=self.tenant_id, patient=patient, encounter=encounter,
                order_type=kind_map[o.kind],
                priority=OrderPriority.STAT if o.priority == "stat" else OrderPriority.ROUTINE,
                status=OrderStatus.COMPLETED, ordered_by="sim:auto", ordered_at=o.ordered_utc)
            Order.objects.filter(pk=order.pk).update(created_at=o.ordered_utc)
            OrderItem.objects.create(tenant_id=self.tenant_id, order=order, code=o.code,
                                     display=o.display, quantity=1)
            txt = f"{o.display}: resulted; TAT {o.tat_min:.0f} min"
            if o.note:
                txt += f" ({o.note})"
            OrderResult.objects.create(
                tenant_id=self.tenant_id, order=order, result_text=txt,
                recorded_at=o.resulted_utc, recorded_by="sim:auto")
            self.counts["orders"] += 1

    # ------------------------------------------------------------------

    def _seed_ed(self):
        from products.cymed.hospital.emergency.models import (
            EmergencyVisit, EmergencyTriage, EmergencyDisposition)
        from products.cymed.core.encounters.models import EncounterParticipant, EncounterStatus
        from products.cymed.core.encounters.models import EncounterType

        nurses = [p for p in self.r.providers if p.ptype == "nurse"]
        self._ed_stay_link = {}
        for v in self.r.ed_visits:
            patient = self.patient_rows.get(v.patient_ref)
            if not patient:
                continue
            sl = H.SL_BY_KEY[v.service_line]
            visit = EmergencyVisit.objects.create(
                tenant_id=self.tenant_id, patient=patient, arrival_method=v.arrival_method,
                presenting_complaint=sl.complaint,
                status={"admitted": "admitted", "transferred": "admitted",
                        "lwbs": "discharged", "discharged": "discharged"}[v.disposition])
            self._backdate(EmergencyVisit, visit.pk, arrival_time=v.arrival_utc,
                           created_at=v.arrival_utc)
            nurse_id = (self.provider_rows[nurses[v.patient_ref % len(nurses)].ref].id
                        if nurses else uuid.uuid4())
            tri = EmergencyTriage.objects.create(
                tenant_id=self.tenant_id, visit=visit, esi_level=v.esi,
                chief_complaint=sl.complaint, triage_nurse_id=nurse_id)
            self._backdate(EmergencyTriage, tri.pk, logged_at=v.arrival_utc + timedelta(minutes=6))
            disp = EmergencyDisposition.objects.create(
                tenant_id=self.tenant_id, visit=visit,
                disposition_type=v.disposition, notes="")
            self._backdate(EmergencyDisposition, disp.pk, logged_at=v.dispo_utc)

            enc = self._make_encounter(patient, EncounterType.EMERGENCY,
                                       EncounterStatus.FINISHED, v.arrival_utc, v.dispo_utc,
                                       self.facility)
            if v.provider_ref in self.provider_rows:
                EncounterParticipant.objects.create(
                    tenant_id=self.tenant_id, encounter=enc,
                    provider=self.provider_rows[v.provider_ref], role="lead")
            self._write_orders(patient, enc, v.orders)
            self.counts["ed_visits"] += 1
        self.log(f"  emergency: {self.counts['ed_visits']} visits")

    def _seed_clinics(self):
        from products.cymed.core.scheduling.models import (
            Appointment, AppointmentParticipant, AppointmentStatus, AppointmentParticipantType)
        from products.cymed.core.encounters.models import (
            Encounter, EncounterParticipant, EncounterStatus, EncounterType)
        status_map = {"fulfilled": AppointmentStatus.FULFILLED,
                      "no_show": AppointmentStatus.CANCELLED,
                      "walk_in": AppointmentStatus.ARRIVED}
        for v in self.r.clinic_visits:
            patient = self.patient_rows.get(v.patient_ref)
            if not patient:
                continue
            fac = self.clinic_facility[v.clinic]
            end = v.end_utc or (v.scheduled_utc + timedelta(minutes=20))
            appt = Appointment.objects.create(
                tenant_id=self.tenant_id, patient=patient,
                appointment_type=H.CLINICS[v.clinic][1], status=status_map[v.status],
                start_time=v.scheduled_utc, end_time=end,
                description=f"{H.CLINICS[v.clinic][0]} - {H.SL_BY_KEY[v.service_line].display}")
            Appointment.objects.filter(pk=appt.pk).update(created_at=v.scheduled_utc - timedelta(days=2))
            AppointmentParticipant.objects.create(
                tenant_id=self.tenant_id, appointment=appt, actor_id=patient.id,
                actor_type=AppointmentParticipantType.choices[0][0], status="accepted")
            if v.provider_ref in self.provider_rows:
                AppointmentParticipant.objects.create(
                    tenant_id=self.tenant_id, appointment=appt,
                    actor_id=self.provider_rows[v.provider_ref].id,
                    actor_type=AppointmentParticipantType.choices[1][0]
                    if len(AppointmentParticipantType.choices) > 1 else
                    AppointmentParticipantType.choices[0][0],
                    status="accepted")
            self.counts["appointments"] += 1

            if v.status == "no_show":
                continue
            enc = self._make_encounter(
                patient, EncounterType.OUTPATIENT, EncounterStatus.FINISHED,
                v.seen_utc or v.scheduled_utc, v.end_utc or end, fac)
            if v.provider_ref in self.provider_rows:
                EncounterParticipant.objects.create(
                    tenant_id=self.tenant_id, encounter=enc,
                    provider=self.provider_rows[v.provider_ref], role="lead")
            self._write_orders(patient, enc, v.orders)
            self.counts["clinic_encounters"] += 1
        self.log(f"  clinics: {self.counts['appointments']} appointments")

    def _seed_inpatient(self):
        from products.cymed.core.encounters.models import (
            EncounterParticipant, EncounterStatus, EncounterType)
        from products.cymed.hospital.adt.models import Admission
        from products.cymed.hospital.inpatient.models import HospitalStay
        from products.cymed.hospital.icu.models import ICUStay
        from products.cymed.hospital.bed_management.models import BedAssignment

        atype, areason = self._admission_refs()
        ward_cursor = defaultdict(int)
        for s in self.r.stays:
            patient = self.patient_rows.get(s.patient_ref)
            if not patient:
                continue
            prov = self.provider_rows.get(s.admitting_provider_ref)
            enc = self._make_encounter(patient, EncounterType.INPATIENT,
                                       EncounterStatus.FINISHED, s.admit_utc, s.discharge_utc,
                                       self.facility)
            if prov:
                EncounterParticipant.objects.create(
                    tenant_id=self.tenant_id, encounter=enc, provider=prov, role="lead")
            adm = Admission.objects.create(
                tenant_id=self.tenant_id, encounter=enc, admission_type=atype,
                admission_reason=areason,
                admitting_physician_id=(prov.id if prov else uuid.uuid4()),
                status="discharged")
            self._backdate(Admission, adm.pk, admitted_at=s.admit_utc, created_at=s.admit_utc)
            stay = HospitalStay.objects.create(
                tenant_id=self.tenant_id, admission=adm,
                care_team_leader_id=(prov.id if prov else uuid.uuid4()),
                expected_length_of_stay=max(1, round(H.SL_BY_KEY[s.service_line].alos_days[0])),
                actual_length_of_stay=max(1, round(s.los_hours / 24)))
            if s.icu:
                icu = ICUStay.objects.create(
                    tenant_id=self.tenant_id, stay=stay,
                    ventilator_status="invasive" if s.service_line in ("cardiac", "neonatal", "general")
                    else "none",
                    invasive_lines_count=1 if s.icu else 0)
                self._backdate(ICUStay, icu.pk, icu_admitted_at=s.icu_admit_utc,
                               icu_released_at=s.icu_release_utc)
                self.counts["icu_stays"] += 1

            beds = self.beds_by_ward.get(s.ward) or []
            if beds:
                bed = beds[ward_cursor[s.ward] % len(beds)]
                ward_cursor[s.ward] += 1
                ba = BedAssignment.objects.create(
                    tenant_id=self.tenant_id, patient=patient, bed=bed,
                    released_at=s.discharge_utc)
                self._backdate(BedAssignment, ba.pk, assigned_at=s.admit_utc)

            self._write_orders(patient, enc, s.orders)
            self.counts["admissions"] += 1
        self.log(f"  inpatient: {self.counts['admissions']} admissions "
                 f"({self.counts['icu_stays']} ICU)")
