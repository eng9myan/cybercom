import uuid
import pytest
from datetime import date
from django.utils import timezone
from rest_framework.test import APIClient
import jwt

from products.cymed.core.patients.models import Patient
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.organizations.models import Organization
from products.cymed.core.facilities.models import Facility, Department, Ward, Room, Bed

from products.cymed.hospital.adt.models import (
    AdmissionReason, AdmissionType, DischargeReason, DischargeDisposition,
    Admission, TransferRequest, TransferApproval, DischargeSummary
)
from products.cymed.hospital.bed_management.models import (
    BedAssignment, BedOccupancy, BedReservation, BedCleaning, BedMaintenance, BedBlocking
)
from products.cymed.hospital.emergency.models import (
    EmergencyVisit, EmergencyTriage, EmergencyAcuity, EmergencyDisposition,
    EmergencyObservation, EmergencyTracking
)
from products.cymed.hospital.inpatient.models import (
    HospitalStay, DailyRound, ProgressReview, InpatientCarePlan, DischargePlanning
)
from products.cymed.hospital.nursing.models import (
    NursingShift, NursingAssignment, NursingAssessment, NursingCarePlan, NursingTask, NursingHandover
)
from products.cymed.hospital.icu.models import (
    ICUStay, ICURound, ICUAssessment, VentilatorRecord, CriticalEvent
)
from products.cymed.hospital.operating_room.models import (
    SurgicalCase, SurgicalSchedule, ProcedureBooking, ProcedureConsent,
    ProcedureChecklist, SurgicalTeam, SurgicalEquipment
)
from products.cymed.hospital.anesthesia.models import (
    AnesthesiaAssessment, AnesthesiaPlan, AnesthesiaRecord, RecoveryAssessment
)
from products.cymed.hospital.maternity.models import (
    Pregnancy, PrenatalEncounter, LaborEpisode, Delivery, NewbornRecord, PostpartumCare
)
from products.cymed.hospital.transfer_center.models import (
    TransferCase, ExternalReferral, AcceptanceReview, ReceivingFacility
)
from products.cymed.hospital.discharge.models import (
    DischargeChecklist, DischargeMedication, FollowUpAppointment, DischargeInstruction
)
from products.cymed.hospital.capacity_management.models import (
    CapacityRule, CapacityThreshold, SurgePlan, OverflowUnit
)

from platform.events.models import OutboxEvent


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def auth_client(test_tenant_id):
    client = APIClient()
    payload = {
        "sub": "33333333-3333-3333-3333-333333333333",
        "email": "doctor@cymed.io",
        "tenant_id": str(test_tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(test_tenant_id),
    )
    return client


@pytest.fixture
def setup_base_data(test_tenant_id):
    org = Organization.objects.create(
        tenant_id=test_tenant_id, name="Hospital Org", slug="hosp-org", organization_type="hospital"
    )
    facility = Facility.objects.create(
        tenant_id=test_tenant_id, organization=org, name="Main Hospital Facility", code="MAIN-HOSP"
    )
    dept = Department.objects.create(
        tenant_id=test_tenant_id, facility=facility, name="Cardiology", code="CARD"
    )
    ward = Ward.objects.create(
        tenant_id=test_tenant_id, department=dept, name="Cardio Ward A", code="CWA"
    )
    room = Room.objects.create(
        tenant_id=test_tenant_id, ward=ward, room_number="101", room_type="standard"
    )
    bed = Bed.objects.create(
        tenant_id=test_tenant_id, room=room, bed_number="101-A", status="available"
    )
    patient = Patient.objects.create(
        tenant_id=test_tenant_id, first_name="Ahmad", last_name="Kamal", dob="1985-05-15", mrn="MRN-H-001"
    )
    encounter = Encounter.objects.create(
        tenant_id=test_tenant_id, patient=patient, encounter_type="inpatient",
        status="in_progress", organization=org, facility=facility
    )
    return {
        "org": org, "facility": facility, "dept": dept,
        "ward": ward, "room": room, "bed": bed,
        "patient": patient, "encounter": encounter
    }


@pytest.mark.django_db
class TestHospitalEdition:

    def test_adt_admission_transfer_discharge_flow(self, auth_client, test_tenant_id, setup_base_data):
        patient = setup_base_data["patient"]
        encounter = setup_base_data["encounter"]
        bed = setup_base_data["bed"]

        adm_reason = AdmissionReason.objects.create(tenant_id=test_tenant_id, name="Chest Pain", code="R-ADM-001")
        adm_type = AdmissionType.objects.create(tenant_id=test_tenant_id, name="Emergency", code="T-ADM-001")
        dis_reason = DischargeReason.objects.create(tenant_id=test_tenant_id, name="Recovered", code="R-DIS-001")
        dis_disp = DischargeDisposition.objects.create(tenant_id=test_tenant_id, name="Home", code="D-DIS-001")

        # Admission
        resp = auth_client.post(
            "/api/v1/hospital/adt/admissions/",
            {
                "encounter": str(encounter.id),
                "admission_type": adm_type.id,
                "admission_reason": adm_reason.id,
                "admitting_physician_id": str(uuid.uuid4()),
                "status": "admitted"
            },
            format="json"
        )
        assert resp.status_code == 201
        admission_id = resp.data["id"]
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.admission.created").count() == 1
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.charge.created", payload__charge_type="admission").count() == 1

        # Transfer Request
        new_bed = Bed.objects.create(tenant_id=test_tenant_id, room=setup_base_data["room"], bed_number="101-B", status="available")
        tx_resp = auth_client.post(
            "/api/v1/hospital/adt/transfer-requests/",
            {
                "patient": str(patient.id),
                "encounter": str(encounter.id),
                "source_bed_id": str(bed.id),
                "target_bed_id": str(new_bed.id),
                "requested_by": str(uuid.uuid4()),
                "reason": "Isolation required",
                "status": "pending"
            },
            format="json"
        )
        assert tx_resp.status_code == 201
        req_id = tx_resp.data["id"]

        # Transfer Approval
        app_resp = auth_client.post(
            "/api/v1/hospital/adt/transfer-approvals/",
            {"transfer_request": req_id, "approved_by": str(uuid.uuid4()), "notes": "Approved"},
            format="json"
        )
        assert app_resp.status_code == 201
        assert TransferRequest.objects.get(id=req_id).status == "approved"
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.transfer.created").count() == 1

        # Discharge
        disc_resp = auth_client.post(
            "/api/v1/hospital/adt/discharge-summaries/",
            {
                "admission": admission_id,
                "discharged_by": str(uuid.uuid4()),
                "disposition": dis_disp.id,
                "reason": dis_reason.id,
                "summary_text": "Patient recovered",
                "instructions": "Rest for 2 weeks"
            },
            format="json"
        )
        assert disc_resp.status_code == 201
        assert Admission.objects.get(id=admission_id).status == "discharged"
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.discharge.completed").count() == 1

    def test_bed_management_operations(self, auth_client, test_tenant_id, setup_base_data):
        bed = setup_base_data["bed"]
        patient = setup_base_data["patient"]

        # Bed Assignment
        assign_resp = auth_client.post(
            "/api/v1/hospital/beds/assignments/",
            {"patient": str(patient.id), "bed": bed.id},
            format="json"
        )
        assert assign_resp.status_code == 201
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.bed.assigned").count() == 1

        # Bed Occupancy
        occ_resp = auth_client.post(
            "/api/v1/hospital/beds/occupancy/",
            {"bed": bed.id, "occupied_date": "2026-06-23", "occupancy_status": "occupied"},
            format="json"
        )
        assert occ_resp.status_code == 201

        # Bed Reservation
        res_resp = auth_client.post(
            "/api/v1/hospital/beds/reservations/",
            {
                "patient": str(patient.id), "bed": bed.id,
                "reserved_from": timezone.now().isoformat(),
                "reserved_to": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
                "status": "pending"
            },
            format="json"
        )
        assert res_resp.status_code == 201

        # Bed Cleaning
        clean_resp = auth_client.post(
            "/api/v1/hospital/beds/cleaning/",
            {"bed": bed.id, "status": "cleaning", "cleaner_name": "Maria"},
            format="json"
        )
        assert clean_resp.status_code == 201

        # Bed Maintenance
        maint_resp = auth_client.post(
            "/api/v1/hospital/beds/maintenance/",
            {"bed": bed.id, "description": "Repair plug", "scheduled_at": timezone.now().isoformat()},
            format="json"
        )
        assert maint_resp.status_code == 201

        # Bed Blocking
        block_resp = auth_client.post(
            "/api/v1/hospital/beds/blocking/",
            {"bed": bed.id, "reason": "Infection control"},
            format="json"
        )
        assert block_resp.status_code == 201

    def test_emergency_visit_triage_acuity_and_alerts(self, auth_client, test_tenant_id, setup_base_data):
        patient = setup_base_data["patient"]

        # Create ED Visit
        visit_resp = auth_client.post(
            "/api/v1/hospital/emergency/visits/",
            {"patient": str(patient.id), "arrival_method": "Ambulance", "presenting_complaint": "Severe dyspnea", "status": "triage"},
            format="json"
        )
        assert visit_resp.status_code == 201
        visit_id = visit_resp.data["id"]
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.charge.created", payload__charge_type="emergency_admission").count() == 1

        # ESI Level 1 Triage -> ICU Alert
        triage_resp = auth_client.post(
            "/api/v1/hospital/emergency/triage/",
            {"visit": visit_id, "esi_level": 1, "chief_complaint": "Unresponsive", "triage_nurse_id": str(uuid.uuid4())},
            format="json"
        )
        assert triage_resp.status_code == 201
        assert EmergencyVisit.objects.get(id=visit_id).status == "resuscitation"
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.icu.alert", payload__alert_type="critical_esi_level_1").count() == 1

        # NEWS2 Acuity >= 5 -> Deterioration Alert
        acuity_resp = auth_client.post(
            "/api/v1/hospital/emergency/acuities/",
            {"visit": visit_id, "news2_score": 6},
            format="json"
        )
        assert acuity_resp.status_code == 201
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.icu.alert", payload__alert_type="high_news2_deterioration").count() == 1

        # Observations, Tracking, Disposition
        obs_resp = auth_client.post(
            "/api/v1/hospital/emergency/observations/",
            {"visit": visit_id, "systolic_bp": 90, "diastolic_bp": 60, "heart_rate": 115, "resp_rate": 26, "temp_c": "38.5", "o2_sat": 92, "notes": "O2 mask applied"},
            format="json"
        )
        assert obs_resp.status_code == 201

        track_resp = auth_client.post(
            "/api/v1/hospital/emergency/tracking/",
            {"visit": visit_id, "location_label": "Resuscitation Bay 1"},
            format="json"
        )
        assert track_resp.status_code == 201

        disp_resp = auth_client.post(
            "/api/v1/hospital/emergency/dispositions/",
            {"visit": visit_id, "disposition_type": "admitted", "notes": "Transferred to Cardiac ICU"},
            format="json"
        )
        assert disp_resp.status_code == 201

    def test_inpatient_stay_and_daily_rounds(self, auth_client, test_tenant_id, setup_base_data):
        adm_reason = AdmissionReason.objects.create(tenant_id=test_tenant_id, name="Dyspnea", code="R-ADM-002")
        adm_type = AdmissionType.objects.create(tenant_id=test_tenant_id, name="Routine", code="T-ADM-002")
        adm = Admission.objects.create(
            tenant_id=test_tenant_id, encounter=setup_base_data["encounter"],
            admission_type=adm_type, admission_reason=adm_reason,
            admitting_physician_id=uuid.uuid4(), status="admitted"
        )

        stay_resp = auth_client.post(
            "/api/v1/hospital/inpatient/stays/",
            {"admission": adm.id, "care_team_leader_id": str(uuid.uuid4()), "expected_length_of_stay": 4},
            format="json"
        )
        assert stay_resp.status_code == 201
        stay_id = stay_resp.data["id"]

        round_resp = auth_client.post(
            "/api/v1/hospital/inpatient/rounds/",
            {
                "stay": stay_id, "clinician_id": str(uuid.uuid4()),
                "subjective_notes": "Chest pain resolved", "objective_notes": "Vitals stable",
                "assessment_notes": "Improving", "plan_notes": "Discharge tomorrow"
            },
            format="json"
        )
        assert round_resp.status_code == 201

        review_resp = auth_client.post(
            "/api/v1/hospital/inpatient/reviews/",
            {"stay": stay_id, "reviewer_id": str(uuid.uuid4()), "progress_status": "improving"},
            format="json"
        )
        assert review_resp.status_code == 201

        # Inpatient care-plans uses "careplans" router path
        cp_resp = auth_client.post(
            "/api/v1/hospital/inpatient/careplans/",
            {"stay": stay_id, "title": "Cardiac Rehab Plan", "goals": "Walking 30min/day", "interventions": "Low sodium diet"},
            format="json"
        )
        assert cp_resp.status_code == 201

        plan_resp = auth_client.post(
            "/api/v1/hospital/inpatient/discharge-planning/",
            {"stay": stay_id, "target_discharge_date": "2026-06-25", "barriers_to_discharge": "", "is_cleared": False},
            format="json"
        )
        assert plan_resp.status_code == 201

    def test_nursing_shifts_and_tasks(self, auth_client, test_tenant_id, setup_base_data):
        adm_reason = AdmissionReason.objects.create(tenant_id=test_tenant_id, name="Asthma", code="R-ADM-NUR-01")
        adm_type = AdmissionType.objects.create(tenant_id=test_tenant_id, name="Elective", code="T-ADM-NUR-01")
        adm = Admission.objects.create(
            tenant_id=test_tenant_id, encounter=setup_base_data["encounter"],
            admission_type=adm_type, admission_reason=adm_reason,
            admitting_physician_id=uuid.uuid4(), status="admitted"
        )

        # Nursing Shift — name, start_time, end_time (TimeField, not DateTimeField)
        shift_resp = auth_client.post(
            "/api/v1/hospital/nursing/shifts/",
            {"name": "Day Shift", "start_time": "07:00:00", "end_time": "15:00:00"},
            format="json"
        )
        assert shift_resp.status_code == 201
        shift_id = shift_resp.data["id"]

        # Nursing Assignment
        assign_resp = auth_client.post(
            "/api/v1/hospital/nursing/assignments/",
            {
                "nurse_id": str(uuid.uuid4()),
                "ward_id": str(setup_base_data["ward"].id),
                "shift": shift_id,
                "assigned_date": "2026-06-23"
            },
            format="json"
        )
        assert assign_resp.status_code == 201
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.employee.synced").count() == 1

        # Nursing Assessment — admission FK, assessed_by, nursing_summary
        assess_resp = auth_client.post(
            "/api/v1/hospital/nursing/assessments/",
            {"admission": adm.id, "assessed_by": str(uuid.uuid4()), "nursing_summary": "Patient stable, lungs clear"},
            format="json"
        )
        assert assess_resp.status_code == 201

        # Nursing Care Plan — admission FK, goals, activities
        cp_resp = auth_client.post(
            "/api/v1/hospital/nursing/careplans/",
            {"admission": adm.id, "goals": "Prevent exacerbation", "activities": "Inhaler schedule, positioning"},
            format="json"
        )
        assert cp_resp.status_code == 201

        # Nursing Task
        task_resp = auth_client.post(
            "/api/v1/hospital/nursing/tasks/",
            {
                "admission": adm.id,
                "task_name": "Nebulizer treatment",
                "scheduled_at": timezone.now().isoformat(),
                "status": "pending"
            },
            format="json"
        )
        assert task_resp.status_code == 201
        task_id = task_resp.data["id"]

        # Complete task -> triggers billing event
        task_patch = auth_client.patch(
            f"/api/v1/hospital/nursing/tasks/{task_id}/",
            {"status": "completed"},
            format="json"
        )
        assert task_patch.status_code == 200

        # Nursing Handover — SBAR format fields
        handover_resp = auth_client.post(
            "/api/v1/hospital/nursing/handovers/",
            {
                "admission": adm.id,
                "outgoing_nurse_id": str(uuid.uuid4()),
                "incoming_nurse_id": str(uuid.uuid4()),
                "situation_background": "Admitted for acute asthma. Responding to nebulizers.",
                "assessment_recommendation": "Lungs improving. Continue 4-hourly nebs."
            },
            format="json"
        )
        assert handover_resp.status_code == 201

    def test_icu_stays_and_critical_events(self, auth_client, test_tenant_id, setup_base_data):
        # Build ICU path: Patient -> Encounter -> Admission -> HospitalStay -> ICUStay
        adm_reason = AdmissionReason.objects.create(tenant_id=test_tenant_id, name="Cardiac Arrest", code="R-ADM-ICU-01")
        adm_type = AdmissionType.objects.create(tenant_id=test_tenant_id, name="ICU Direct", code="T-ADM-ICU-01")
        adm = Admission.objects.create(
            tenant_id=test_tenant_id, encounter=setup_base_data["encounter"],
            admission_type=adm_type, admission_reason=adm_reason,
            admitting_physician_id=uuid.uuid4(), status="admitted"
        )
        inpatient_stay = HospitalStay.objects.create(
            tenant_id=test_tenant_id, admission=adm, care_team_leader_id=uuid.uuid4()
        )

        # ICU Stay — linked via HospitalStay
        stay_resp = auth_client.post(
            "/api/v1/hospital/icu/stays/",
            {"stay": inpatient_stay.id, "ventilator_status": "invasive", "invasive_lines_count": 2},
            format="json"
        )
        assert stay_resp.status_code == 201
        icu_id = stay_resp.data["id"]
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.charge.created", payload__charge_type="icu_room").count() == 1

        # ICU Round — heart_rate, mean_arterial_pressure, temp_c, resp_rate, o2_sat
        round_resp = auth_client.post(
            "/api/v1/hospital/icu/rounds/",
            {
                "icu_stay": icu_id, "recorded_by": str(uuid.uuid4()),
                "heart_rate": 88, "mean_arterial_pressure": 75,
                "temp_c": "37.2", "resp_rate": 18, "o2_sat": 97
            },
            format="json"
        )
        assert round_resp.status_code == 201

        # ICU Assessment — sofa_score, apache_ii_score, glasgow_coma_scale
        assess_resp = auth_client.post(
            "/api/v1/hospital/icu/assessments/",
            {"icu_stay": icu_id, "sofa_score": 4, "apache_ii_score": 12, "glasgow_coma_scale": 13},
            format="json"
        )
        assert assess_resp.status_code == 201

        # Ventilator Record — mode, fio2_pct, peep, rate, logged_by
        vent_resp = auth_client.post(
            "/api/v1/hospital/icu/ventilators/",
            {"icu_stay": icu_id, "logged_by": str(uuid.uuid4()), "mode": "ACMV", "fio2_pct": 40, "peep": 5, "rate": 14},
            format="json"
        )
        assert vent_resp.status_code == 201

        # Critical Event — event_type, details, actions_taken
        crit_resp = auth_client.post(
            "/api/v1/hospital/icu/critical-events/",
            {"icu_stay": icu_id, "event_type": "vent_failure", "details": "Vent disconnected", "actions_taken": "Reconnected and sealed"},
            format="json"
        )
        assert crit_resp.status_code == 201
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.icu.alert", payload__alert_type="critical_event_vent_failure").count() == 1

    def test_operating_room_surgical_case_flow(self, auth_client, test_tenant_id, setup_base_data):
        patient = setup_base_data["patient"]

        # Valid SNOMED code
        case_resp = auth_client.post(
            "/api/v1/hospital/or/cases/",
            {
                "patient": str(patient.id), "surgeon_id": str(uuid.uuid4()),
                "procedure_code": "371038006",
                "scheduled_start": timezone.now().isoformat(),
                "scheduled_end": (timezone.now() + timezone.timedelta(hours=2)).isoformat(),
                "status": "scheduled"
            },
            format="json"
        )
        assert case_resp.status_code == 201
        case_id = case_resp.data["id"]

        # Invalid code -> validation error
        bad_resp = auth_client.post(
            "/api/v1/hospital/or/cases/",
            {
                "patient": str(patient.id), "surgeon_id": str(uuid.uuid4()),
                "procedure_code": "INVALID-CODE",
                "scheduled_start": timezone.now().isoformat(),
                "scheduled_end": (timezone.now() + timezone.timedelta(hours=2)).isoformat(),
                "status": "scheduled"
            },
            format="json"
        )
        assert bad_resp.status_code == 400

        # Schedule
        sched_resp = auth_client.post(
            "/api/v1/hospital/or/schedules/",
            {"surgical_case": case_id, "operating_room_id": str(uuid.uuid4()), "allocated_date": "2026-06-23"},
            format="json"
        )
        assert sched_resp.status_code == 201

        # Booking
        book_resp = auth_client.post(
            "/api/v1/hospital/or/bookings/",
            {"surgical_case": case_id, "priority": "elective"},
            format="json"
        )
        assert book_resp.status_code == 201

        # Consent
        consent_resp = auth_client.post(
            "/api/v1/hospital/or/consents/",
            {"surgical_case": case_id, "patient_signature_blob": "Base64==", "witness_name": "Nurse Kelly"},
            format="json"
        )
        assert consent_resp.status_code == 201

        # WHO Checklist
        chk_resp = auth_client.post(
            "/api/v1/hospital/or/checklists/",
            {"surgical_case": case_id, "sign_in_ok": True, "time_out_ok": True, "sign_out_ok": True},
            format="json"
        )
        assert chk_resp.status_code == 201

        # Team
        team_resp = auth_client.post(
            "/api/v1/hospital/or/teams/",
            {"surgical_case": case_id, "member_id": str(uuid.uuid4()), "role": "lead_surgeon"},
            format="json"
        )
        assert team_resp.status_code == 201

        # Equipment -> asset.assigned outbox
        eq_resp = auth_client.post(
            "/api/v1/hospital/or/equipment/",
            {"surgical_case": case_id, "asset_serial": "SRG-MTR-988", "sterilized_status": True},
            format="json"
        )
        assert eq_resp.status_code == 201
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.asset.assigned").count() == 1

        # Complete case -> surgery.completed + billing + inventory
        patch_resp = auth_client.patch(
            f"/api/v1/hospital/or/cases/{case_id}/",
            {"status": "completed"},
            format="json"
        )
        assert patch_resp.status_code == 200
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.hospital.surgery.completed").count() == 1
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.charge.created", payload__charge_type="or_utilization").count() == 1
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.inventory.consumed").count() == 1

    def test_anesthesia_records_and_aldrete_scoring(self, auth_client, test_tenant_id, setup_base_data):
        patient = setup_base_data["patient"]
        case = SurgicalCase.objects.create(
            tenant_id=test_tenant_id, patient=patient, surgeon_id=uuid.uuid4(),
            procedure_code="371038006",
            scheduled_start=timezone.now(), scheduled_end=timezone.now() + timezone.timedelta(hours=1),
            status="intra_op"
        )

        assess_resp = auth_client.post(
            "/api/v1/hospital/anesthesia/assessments/",
            {"surgical_case": case.id, "assessed_by": str(uuid.uuid4()), "asa_class": "ASA II", "airway_mallampati": 2, "notes": "Mild smoker"},
            format="json"
        )
        assert assess_resp.status_code == 201

        plan_resp = auth_client.post(
            "/api/v1/hospital/anesthesia/plans/",
            {"surgical_case": case.id, "anesthetic_type": "general", "plan_description": "Propofol induction"},
            format="json"
        )
        assert plan_resp.status_code == 201

        rec_resp = auth_client.post(
            "/api/v1/hospital/anesthesia/records/",
            {
                "surgical_case": case.id, "anesthesiologist_id": str(uuid.uuid4()),
                "start_time": timezone.now().isoformat(), "agents_used": ["Propofol", "Sevoflurane"], "notes": "Tolerated well"
            },
            format="json"
        )
        assert rec_resp.status_code == 201

        # Recovery — URL is "recovery-assessments/" not "recovery/"
        rec_assess_resp = auth_client.post(
            "/api/v1/hospital/anesthesia/recovery-assessments/",
            {"surgical_case": case.id, "aldrete_score": 9, "comments": "Fully conscious"},
            format="json"
        )
        assert rec_assess_resp.status_code == 201
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.charge.created", payload__charge_type="anesthesia_recovery").count() == 1

    def test_maternity_records_and_newborn(self, auth_client, test_tenant_id, setup_base_data):
        patient = setup_base_data["patient"]

        # Pregnancy — estimated_delivery_date, gravidity, parity
        preg_resp = auth_client.post(
            "/api/v1/hospital/maternity/pregnancies/",
            {"patient": str(patient.id), "estimated_delivery_date": "2026-07-15", "gravidity": 2, "parity": 1, "status": "active"},
            format="json"
        )
        assert preg_resp.status_code == 201
        preg_id = preg_resp.data["id"]

        # Prenatal Encounter — maternal_bp_sys/dia as separate fields
        prenatal_resp = auth_client.post(
            "/api/v1/hospital/maternity/prenatal-encounters/",
            {"pregnancy": preg_id, "gestational_weeks": "36.0", "fetal_heart_rate": 140, "maternal_bp_sys": 110, "maternal_bp_dia": 70, "notes": "Cephalic"},
            format="json"
        )
        assert prenatal_resp.status_code == 201

        # Labor Episode
        labor_resp = auth_client.post(
            "/api/v1/hospital/maternity/labor-episodes/",
            {"pregnancy": preg_id, "stage_of_labor": 1, "cervical_dilation_cm": "4.0", "fetal_monitoring_status": "normal"},
            format="json"
        )
        assert labor_resp.status_code == 201
        labor_id = labor_resp.data["id"]

        # Delivery — delivery_time, delivery_method, apgar_1m, apgar_5m
        delivery_resp = auth_client.post(
            "/api/v1/hospital/maternity/deliveries/",
            {
                "labor_episode": labor_id,
                "delivery_time": timezone.now().isoformat(),
                "delivery_method": "vaginal",
                "apgar_1m": 8, "apgar_5m": 9, "outcome": "live_birth"
            },
            format="json"
        )
        assert delivery_resp.status_code == 201
        delivery_id = delivery_resp.data["id"]

        # Newborn — weight_grams, height_cm, head_circumference_cm
        newborn_resp = auth_client.post(
            "/api/v1/hospital/maternity/newborns/",
            {"delivery": delivery_id, "gender": "female", "weight_grams": 3250, "height_cm": "50.0", "head_circumference_cm": "34.0"},
            format="json"
        )
        assert newborn_resp.status_code == 201

        # Postpartum Care — checked_by, maternal_condition, baby_condition
        post_resp = auth_client.post(
            "/api/v1/hospital/maternity/postpartum-checks/",
            {"pregnancy": preg_id, "checked_by": str(uuid.uuid4()), "maternal_condition": "Stable", "baby_condition": "Healthy"},
            format="json"
        )
        assert post_resp.status_code == 201

    def test_transfer_center_and_referrals(self, auth_client, test_tenant_id, setup_base_data):
        patient = setup_base_data["patient"]

        # ReceivingFacility — name, code, facility_type (all required)
        fac_resp = auth_client.post(
            "/api/v1/hospital/transfer-center/facilities/",
            {"name": "King Hussein Cancer Center", "code": "KHCC-AMM", "facility_type": "hospital"},
            format="json"
        )
        assert fac_resp.status_code == 201
        fac_id = fac_resp.data["id"]

        # TransferCase — patient, source_hospital_name, target_facility, reason
        case_resp = auth_client.post(
            "/api/v1/hospital/transfer-center/cases/",
            {"patient": str(patient.id), "source_hospital_name": "Al-Khalidi Hospital", "target_facility": fac_id, "reason": "Oncology evaluation"},
            format="json"
        )
        assert case_resp.status_code == 201
        case_id = case_resp.data["id"]

        # AcceptanceReview — reviewed_by, decision, notes
        review_resp = auth_client.post(
            "/api/v1/hospital/transfer-center/reviews/",
            {"transfer_case": case_id, "reviewed_by": str(uuid.uuid4()), "decision": "accept", "notes": "Accepted"},
            format="json"
        )
        assert review_resp.status_code == 201

        # ExternalReferral — transfer_case, referring_physician_name
        ref_resp = auth_client.post(
            "/api/v1/hospital/transfer-center/referrals/",
            {"transfer_case": case_id, "referring_physician_name": "Dr. Hani Salem"},
            format="json"
        )
        assert ref_resp.status_code == 201

    def test_discharge_medication_validations(self, auth_client, test_tenant_id, setup_base_data):
        adm_reason = AdmissionReason.objects.create(tenant_id=test_tenant_id, name="Dyspnea", code="R-ADM-003")
        adm_type = AdmissionType.objects.create(tenant_id=test_tenant_id, name="Emergency", code="T-ADM-003")
        adm = Admission.objects.create(
            tenant_id=test_tenant_id, encounter=setup_base_data["encounter"],
            admission_type=adm_type, admission_reason=adm_reason,
            admitting_physician_id=uuid.uuid4(), status="admitted"
        )
        stay = HospitalStay.objects.create(tenant_id=test_tenant_id, admission=adm, care_team_leader_id=uuid.uuid4())

        # Discharge Checklist
        chk_resp = auth_client.post(
            "/api/v1/hospital/discharge/checklists/",
            {"stay": stay.id, "task_name": "billing_cleared", "status": "pending"},
            format="json"
        )
        assert chk_resp.status_code == 201
        chk_id = chk_resp.data["id"]

        # Complete checklist -> billing event
        patch_resp = auth_client.patch(
            f"/api/v1/hospital/discharge/checklists/{chk_id}/",
            {"status": "completed"},
            format="json"
        )
        assert patch_resp.status_code == 200
        assert OutboxEvent.objects.filter(tenant_id=test_tenant_id, event_type="cymed.charge.created", payload__charge_type="discharge_processing").count() == 1

        # Valid SNOMED medication code
        med_resp = auth_client.post(
            "/api/v1/hospital/discharge/medications/",
            {"stay": stay.id, "medication_code": "111553001", "reconciliation_action": "continued", "notes": "Daily"},
            format="json"
        )
        assert med_resp.status_code == 201

        # Invalid medication code
        bad_med = auth_client.post(
            "/api/v1/hospital/discharge/medications/",
            {"stay": stay.id, "medication_code": "INVALID-MED", "reconciliation_action": "continued"},
            format="json"
        )
        assert bad_med.status_code == 400

        # Follow Up — specialty_code, target_date
        follow_resp = auth_client.post(
            "/api/v1/hospital/discharge/followups/",
            {"stay": stay.id, "specialty_code": "CARD", "target_date": "2026-07-01"},
            format="json"
        )
        assert follow_resp.status_code == 201

        # Discharge Instruction
        inst_resp = auth_client.post(
            "/api/v1/hospital/discharge/instructions/",
            {"stay": stay.id, "dietary_instructions": "Low fat", "warning_symptoms": "Return if chest pain recurs"},
            format="json"
        )
        assert inst_resp.status_code == 201

    def test_clinical_command_center_metrics(self, auth_client, test_tenant_id, setup_base_data):
        metrics_resp = auth_client.get("/api/v1/hospital/command-center/metrics/")
        assert metrics_resp.status_code == 200
        assert "operational_census" in metrics_resp.data
        assert "capacity_indicators" in metrics_resp.data
        assert "staffing_compliance" in metrics_resp.data

    def test_capacity_management_surge_planning(self, auth_client, test_tenant_id, setup_base_data):
        # CapacityRule — rule_name, metric_source, threshold_value, action_plan_name
        rule_resp = auth_client.post(
            "/api/v1/hospital/capacity/rules/",
            {"rule_name": "Quarantine Surge", "metric_source": "census", "threshold_value": 90, "action_plan_name": "Overflow Protocol"},
            format="json"
        )
        assert rule_resp.status_code == 201
        rule_id = rule_resp.data["id"]

        # CapacityThreshold — rule FK, current_value, status_level
        thr_resp = auth_client.post(
            "/api/v1/hospital/capacity/thresholds/",
            {"rule": rule_id, "current_value": 85, "status_level": "warning"},
            format="json"
        )
        assert thr_resp.status_code == 201

        # SurgePlan — name, trigger_condition, allocated_beds_count, is_active
        surge_resp = auth_client.post(
            "/api/v1/hospital/capacity/surge-plans/",
            {"name": "Mass Casualty L1", "trigger_condition": "5+ critical", "allocated_beds_count": 20, "is_active": False},
            format="json"
        )
        assert surge_resp.status_code == 201

        # OverflowUnit — name, temporary_capacity, current_occupancy, is_open
        overflow_resp = auth_client.post(
            "/api/v1/hospital/capacity/overflow-units/",
            {"name": "West Overflow B", "temporary_capacity": 20, "current_occupancy": 0, "is_open": True},
            format="json"
        )
        assert overflow_resp.status_code == 201
