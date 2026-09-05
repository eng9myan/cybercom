"""
Deterministic hospital + clinic-network operations engine.

Given a seed, a start date and a scenario variant it produces a full week of:
emergency arrivals (triage -> provider -> disposition), outpatient clinic
sessions, inpatient admissions (ED + direct) with bed assignment, ICU and
discharge, and lab / imaging / pharmacy orders with turnaround. It tracks ward
bed capacity so a full ward boards patients and a scanner outage actually
stretches imaging turnaround.

No database access here; `seeder.HospitalSeeder` writes the result.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .scenarios import hospital as H

UTC = ZoneInfo("UTC")
TZ = ZoneInfo(H.TIMEZONE)

_FIRST_M = ["Ahmad", "Mohammad", "Omar", "Yousef", "Khaled", "Sami", "Tariq", "Nabil", "HADI", "Rami"]
_FIRST_F = ["Fatima", "Sara", "Rania", "Mona", "Layla", "Huda", "Dina", "Aya", "Noor", "Salma"]
_LAST = ["Al-Zoubi", "Haddad", "Nazzal", "Khoury", "Al-Masri", "Saleh", "Odeh", "Barakat",
         "Al-Rashid", "Mansour", "Darwish", "Hijazi", "Qasem", "Sabbagh"]


def _rng(*parts) -> random.Random:
    return random.Random("|".join(str(p) for p in parts))


def _pick(rng, mapping: dict):
    items = list(mapping)
    return _weighted(rng, items, [mapping[i] for i in items])


def _weighted(rng, items, weights):
    tot = sum(weights)
    if tot <= 0:
        return rng.choice(items)
    r = rng.random() * tot
    upto = 0.0
    for it, w in zip(items, weights):
        upto += w
        if upto >= r:
            return it
    return items[-1]


# ---------------------------------------------------------------------------
# result types
# ---------------------------------------------------------------------------


@dataclass
class ProviderRec:
    ref: int
    first: str
    last: str
    ptype: str          # physician | nurse
    specialty: str
    npi: str


@dataclass
class PatientRec:
    ref: int
    first: str
    last: str
    dob: date
    gender: str
    mrn: str
    national_id: str
    service_line: str


@dataclass
class SimOrder:
    kind: str           # lab | imaging | medication
    code: str
    display: str
    priority: str       # routine | stat
    context: str        # ED | inpatient | clinic
    service_line: str
    ordered_utc: datetime
    resulted_utc: datetime
    turnaround_min: float
    cost: float
    note: str = ""

    @property
    def tat_min(self) -> float:
        return (self.resulted_utc - self.ordered_utc).total_seconds() / 60.0


@dataclass
class EDVisit:
    patient_ref: int
    service_line: str
    arrival_method: str
    esi: int
    arrival_utc: datetime
    seen_utc: datetime | None
    disposition: str          # discharged | admitted | transferred | lwbs
    dispo_utc: datetime
    provider_ref: int
    orders: list[SimOrder] = field(default_factory=list)

    @property
    def door_to_provider_min(self) -> float | None:
        if not self.seen_utc:
            return None
        return (self.seen_utc - self.arrival_utc).total_seconds() / 60.0

    @property
    def door_to_dispo_min(self) -> float:
        return (self.dispo_utc - self.arrival_utc).total_seconds() / 60.0


@dataclass
class ClinicVisit:
    patient_ref: int
    clinic: str
    service_line: str
    provider_ref: int
    scheduled_utc: datetime
    status: str               # fulfilled | no_show | walk_in
    arrived_utc: datetime | None
    seen_utc: datetime | None
    end_utc: datetime | None
    orders: list[SimOrder] = field(default_factory=list)


@dataclass
class InpatientStay:
    patient_ref: int
    service_line: str
    source: str               # ED | direct
    ward: str
    admit_utc: datetime
    discharge_utc: datetime
    icu: bool
    icu_admit_utc: datetime | None
    icu_release_utc: datetime | None
    admitting_provider_ref: int
    boarding_min: float
    orders: list[SimOrder] = field(default_factory=list)

    @property
    def los_hours(self) -> float:
        return (self.discharge_utc - self.admit_utc).total_seconds() / 3600.0


@dataclass
class SimResult:
    scenario: str
    variant_label: str
    seed: int
    start_date: date
    days: int
    scale: float
    providers: list[ProviderRec] = field(default_factory=list)
    patients: list[PatientRec] = field(default_factory=list)
    ed_visits: list[EDVisit] = field(default_factory=list)
    clinic_visits: list[ClinicVisit] = field(default_factory=list)
    stays: list[InpatientStay] = field(default_factory=list)
    disruption_log: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------------


class HospitalSimulator:
    def __init__(self, *, seed: int, start_date: date, days: int = 7,
                 variant: str = "baseline", scale: float = 1.0):
        self.seed = seed
        self.start_date = start_date
        self.days = days
        self.variant_name = variant
        self.variant = H.variant(variant)
        self.scale = scale
        self.result = SimResult(scenario="hospital", variant_label=self.variant["label"],
                                seed=seed, start_date=start_date, days=days, scale=scale)
        self._providers_by_specialty: dict[str, list[ProviderRec]] = {}
        self._nurses: list[ProviderRec] = []
        self._patient_pool: list[PatientRec] = []
        self._ward_release: dict[str, list[datetime]] = {w: [] for w in H.WARDS}
        self._next_patient = 0

    # -- setup ---------------------------------------------------------

    def _build_providers(self):
        ref = 0
        for spec, (display, n_phys, n_nurse) in H.SPECIALTIES.items():
            plist = []
            for i in range(max(1, round(n_phys * max(self.scale, 0.4)))):
                rng = _rng(self.seed, "phys", spec, i)
                male = rng.random() < 0.62
                p = ProviderRec(ref, rng.choice(_FIRST_M if male else _FIRST_F),
                                rng.choice(_LAST), "physician", spec,
                                f"NPI-{self.seed % 100000:05d}-{ref:04d}")
                plist.append(p)
                self.result.providers.append(p)
                ref += 1
            self._providers_by_specialty[spec] = plist
            for i in range(max(1, round(n_nurse * max(self.scale, 0.4)))):
                rng = _rng(self.seed, "nurse", spec, i)
                male = rng.random() < 0.2
                p = ProviderRec(ref, rng.choice(_FIRST_M if male else _FIRST_F),
                                rng.choice(_LAST), "nurse", spec,
                                f"NPI-{self.seed % 100000:05d}-{ref:04d}")
                self._nurses.append(p)
                self.result.providers.append(p)
                ref += 1

    def _build_patient_pool(self):
        # generous pool; encounters draw from it with reuse
        est = int((H.ED_ARRIVALS_PER_DAY + 130) * self.days * self.scale * 0.8)
        for i in range(max(50, est)):
            rng = _rng(self.seed, "pt", i)
            male = rng.random() < 0.5
            sl = _weighted(rng, [s.key for s in H.SERVICE_LINES],
                           [s.clinic_share + s.ed_share for s in H.SERVICE_LINES])
            if sl == "neonatal":
                age_days = rng.randint(0, 28)
                dob = self.start_date - timedelta(days=age_days)
            elif sl == "pediatric":
                dob = self.start_date - timedelta(days=rng.randint(365, 365 * 15))
            elif sl == "obstetric":
                male = False
                dob = self.start_date - timedelta(days=rng.randint(365 * 18, 365 * 44))
            else:
                dob = self.start_date - timedelta(days=rng.randint(365 * 18, 365 * 92))
            p = PatientRec(i, rng.choice(_FIRST_M if male else _FIRST_F), rng.choice(_LAST),
                           dob, "male" if male else "female",
                           f"CUSH-{self.seed % 1000:03d}-{i:06d}",
                           f"{rng.randint(1, 9)}{rng.randint(0, 9999999999):010d}",
                           sl)
            self._patient_pool.append(p)
            self.result.patients.append(p)

    def _patient_for(self, rng, service_line: str) -> PatientRec:
        matching = [p for p in self._patient_pool if p.service_line == service_line]
        return rng.choice(matching or self._patient_pool)

    # -- disruptions -------------------------------------------------

    def _disruptions_for(self, di: int):
        return [d for d in self.variant.get("disruptions", ()) if di in d.day_index]

    # -- main ------------------------------------------------------

    def run(self) -> SimResult:
        self._build_providers()
        self._build_patient_pool()
        for di in range(self.days):
            day = self.start_date + timedelta(days=di)
            disruptions = self._disruptions_for(di)
            self._run_ed_day(day, di, disruptions)
            self._run_clinics_day(day, di, disruptions)
            self._run_direct_admissions(day, di, disruptions)
        self.result.disruption_log = [
            f"day {d.day_index[0] + 1}-{d.day_index[-1] + 1}: {d.kind}"
            f"{(' ' + d.target) if d.target else ''} - {d.note}"
            for d in self.variant.get("disruptions", ())
        ]
        return self.result

    # -- emergency department -------------------------------------

    def _run_ed_day(self, day, di, disruptions):
        rng = _rng(self.seed, "ed", di)
        base = H.ED_ARRIVALS_PER_DAY * H.ED_WEEKDAY_FACTOR[day.weekday()] * self.scale
        for d in disruptions:
            if d.kind == "ed_surge":
                base *= (1.0 + d.magnitude)
        n = max(0, int(rng.gauss(base, math.sqrt(max(base, 1)))))

        ct_down = any(d.kind == "modality_down" and d.target == "CT" for d in disruptions)
        drug_out = set()
        for d in disruptions:
            if d.kind == "drug_stockout":
                drug_out.update(d.target.split(","))

        # ED "in department" load, used for crowding-driven waits + LWBS
        in_dept: list[datetime] = []          # dispo times of patients still there
        hours = list(H.ED_HOURLY_WEIGHTS)
        hw = [H.ED_HOURLY_WEIGHTS[h] for h in hours]

        arrivals = []
        for _ in range(n):
            hour = _weighted(rng, hours, hw)
            arr_local = datetime.combine(day, time(hour, rng.randint(0, 59), rng.randint(0, 59)), tzinfo=TZ)
            arrivals.append(arr_local.astimezone(UTC))
        arrivals.sort()

        for arr in arrivals:
            in_dept = [t for t in in_dept if t > arr]
            crowd = len(in_dept) / H.WARDS["ED"][2]        # >1 == over capacity

            method = _pick(rng, H.ED_ARRIVAL_METHODS)
            sl = _weighted(rng, [s.key for s in H.SERVICE_LINES],
                           [s.ed_share for s in H.SERVICE_LINES])
            spec = H.SL_BY_KEY[sl].specialty
            esi = int(_pick(rng, H.ESI_MIX[method]))
            pt = self._patient_for(rng, sl)

            # wait to provider: base by ESI, stretched by crowding
            base_wait = {1: 2, 2: 12, 3: 35, 4: 55, 5: 70}[esi]
            wait_min = base_wait * (1.0 + 1.8 * max(0.0, crowd - 0.6)) * rng.uniform(0.7, 1.5)

            lwbs_p = (H.LWBS_BASE_RATE + 0.09 * max(0.0, crowd - 0.8)) if esi >= 4 else 0.0
            if rng.random() < lwbs_p:
                dispo_utc = arr + timedelta(minutes=wait_min * rng.uniform(0.6, 1.1))
                self.result.ed_visits.append(EDVisit(
                    pt.ref, sl, method, esi, arr, None, "lwbs", dispo_utc, -1, []))
                in_dept.append(dispo_utc)
                continue

            seen_utc = arr + timedelta(minutes=wait_min)
            prov = rng.choice(self._providers_by_specialty.get("emergency_medicine")
                              or self.result.providers)
            slc = H.SL_BY_KEY[sl]
            stat = esi <= 2
            orders = self._ed_orders(rng, slc, seen_utc, esi, stat, ct_down, drug_out, di)

            target = H.ED_DISPO_TARGET_MIN[esi]
            work_min = target * (0.55 + 0.5 * rng.random()) * (1.0 + 0.9 * max(0.0, crowd - 0.7))
            # disposition waits on fast results only — cultures / send-outs come
            # back after the patient has left or been admitted.
            fast = [o.tat_min for o in orders if o.tat_min <= 180]
            if fast:
                work_min = max(work_min, max(fast) + rng.uniform(10, 45))
            dispo_utc = seen_utc + timedelta(minutes=work_min)

            admit_p = slc.admit_rate * {1: 1.8, 2: 1.4, 3: 1.0, 4: 0.35, 5: 0.1}[esi]
            if rng.random() < min(0.95, admit_p):
                disposition = "transferred" if rng.random() < 0.04 else "admitted"
            else:
                disposition = "discharged"

            self.result.ed_visits.append(EDVisit(
                pt.ref, sl, method, esi, arr, seen_utc, disposition, dispo_utc, prov.ref, orders))
            in_dept.append(dispo_utc)

            if disposition == "admitted":
                self._admit(rng, pt, sl, "ED", dispo_utc, di, disruptions, seed_orders=orders)

    def _ed_orders(self, rng, slc, t0, esi, stat, ct_down, drug_out, di):
        out = []
        n_lab = 1 if esi >= 4 else rng.randint(2, 4)
        for code in rng.sample(list(slc.lab_codes), min(n_lab, len(slc.lab_codes))):
            out.append(self._make_order(rng, "lab", code, t0, stat, "ED", slc.key, ct_down, drug_out))
        if rng.random() < (0.85 if esi <= 3 else 0.4):
            code = rng.choice(slc.img_codes)
            out.append(self._make_order(rng, "imaging", code, t0, stat, "ED", slc.key, ct_down, drug_out))
        if rng.random() < 0.7:
            code = rng.choice(slc.rx_codes)
            out.append(self._make_order(rng, "medication", code, t0, stat, "ED", slc.key, ct_down, drug_out))
        return out

    def _make_order(self, rng, kind, code, t0, stat, context, sl, ct_down, drug_out):
        if kind == "lab":
            spec = H.LAB_BY_CODE[code]
        elif kind == "imaging":
            spec = H.IMG_BY_CODE[code]
        else:
            spec = H.RX_BY_CODE[code]
        tat = spec.turnaround[1] if stat else spec.turnaround[0]
        tat *= rng.uniform(0.8, 1.6)
        note = ""
        if kind == "imaging" and ct_down and getattr(spec, "modality", "") == "CT":
            tat *= rng.uniform(4.5, 8.0)
            note = "CT scanner down — study delayed / outsourced"
        if kind == "medication" and code in drug_out:
            tat *= rng.uniform(3.0, 5.0)
            note = "drug on backorder — substituted / delayed"
        ordered = t0 + timedelta(minutes=rng.uniform(1, 20))
        return SimOrder(kind, code, spec.name, "stat" if stat else "routine", context, sl,
                        ordered, ordered + timedelta(minutes=tat), round(tat, 1),
                        round(spec.cost, 2), note)

    # -- clinics --------------------------------------------------

    def _run_clinics_day(self, day, di, disruptions):
        if day.weekday() not in H.CLINIC_SESSION_DAYS:
            return
        ct_down = any(d.kind == "modality_down" and d.target == "CT" for d in disruptions)
        drug_out = set()
        for d in disruptions:
            if d.kind == "drug_stockout":
                drug_out.update(d.target.split(","))

        for clinic_code, (display, spec, rooms, slots) in H.CLINICS.items():
            providers = self._providers_by_specialty.get(spec) or []
            n_prov = max(1, min(len(providers), round(rooms * max(self.scale, 0.4))))
            sl = next((s for s in H.SERVICE_LINES if s.clinic == clinic_code), H.SL_BY_KEY["general"])
            for pi in range(n_prov):
                prov = providers[pi % len(providers)] if providers else None
                rng = _rng(self.seed, "clinic", clinic_code, pi, di)
                n_slots = max(1, round(slots * max(self.scale, 0.4)))
                for s in range(n_slots):
                    start_local = datetime.combine(day, time(8, 0), tzinfo=TZ) + timedelta(minutes=20 * s)
                    sched = start_local.astimezone(UTC)
                    pt = self._patient_for(rng, sl.key)
                    if rng.random() < H.CLINIC_NOSHOW_RATE:
                        self.result.clinic_visits.append(ClinicVisit(
                            pt.ref, clinic_code, sl.key, prov.ref if prov else -1,
                            sched, "no_show", None, None, None, []))
                        continue
                    arrived = sched + timedelta(minutes=rng.uniform(-12, 25))
                    seen = max(arrived, sched) + timedelta(minutes=rng.uniform(2, 30))
                    end = seen + timedelta(minutes=rng.uniform(10, 28))
                    orders = []
                    if rng.random() < H.CLINIC_ORDER_RATE:
                        for _ in range(rng.randint(1, 3)):
                            kind = _weighted(rng, ["lab", "imaging", "medication"], [0.55, 0.2, 0.25])
                            code = (rng.choice(sl.lab_codes) if kind == "lab"
                                    else rng.choice(sl.img_codes) if kind == "imaging"
                                    else rng.choice(sl.rx_codes))
                            orders.append(self._make_order(rng, kind, code, seen, False,
                                                           "clinic", sl.key, ct_down, drug_out))
                    self.result.clinic_visits.append(ClinicVisit(
                        pt.ref, clinic_code, sl.key, prov.ref if prov else -1,
                        sched, "fulfilled", arrived, seen, end, orders))
                # walk-ins
                for _ in range(int(rng.gauss(n_slots * H.CLINIC_WALKIN_RATE, 1))):
                    at_local = datetime.combine(day, time(rng.randint(8, 15), rng.randint(0, 59)), tzinfo=TZ)
                    at = at_local.astimezone(UTC)
                    pt = self._patient_for(rng, sl.key)
                    seen = at + timedelta(minutes=rng.uniform(15, 90))
                    self.result.clinic_visits.append(ClinicVisit(
                        pt.ref, clinic_code, sl.key, prov.ref if prov else -1,
                        at, "walk_in", at, seen, seen + timedelta(minutes=rng.uniform(10, 25)), []))

    # -- admissions ---------------------------------------------

    def _run_direct_admissions(self, day, di, disruptions):
        rng = _rng(self.seed, "direct", di)
        for sl in H.SERVICE_LINES:
            n = max(0, int(rng.gauss(sl.direct_admits_per_day * self.scale,
                                     math.sqrt(max(sl.direct_admits_per_day, 1)))))
            for _ in range(n):
                hour = rng.randint(7, 20)
                t = datetime.combine(day, time(hour, rng.randint(0, 59)), tzinfo=TZ).astimezone(UTC)
                pt = self._patient_for(rng, sl.key)
                self._admit(rng, pt, sl.key, "direct", t, di, disruptions)

    def _admit(self, rng, pt, sl_key, source, when, di, disruptions, seed_orders=None):
        sl = H.SL_BY_KEY[sl_key]
        icu = rng.random() < sl.icu_rate
        ward = sl.ward if not icu else ("NICU" if sl_key == "neonatal" else
                                        "CCU" if sl_key == "cardiac" else "ICU")

        staffing_pen = 1.0
        for d in disruptions:
            if d.kind == "ward_staffing" and d.target == ward:
                staffing_pen = 1.0 + d.magnitude * 0.7

        cap = H.WARDS[ward][2]
        rel = [t for t in self._ward_release[ward] if t > when]
        self._ward_release[ward] = rel
        # The patient is admitted at `when`; when the target ward is full they
        # hold in the ED / a flex bed first (boarding_min) and census is allowed
        # to run slightly over cap, as it does in reality — no admit cascade.
        boarding_min = 0.0
        if len(rel) >= cap:
            overage = len(rel) - cap + 1
            boarding_min = min(720.0, 75.0 * overage * rng.uniform(0.6, 1.5))
        admit_utc = when

        mean, sd = sl.alos_days
        los_days = max(0.3, rng.gauss(mean, sd)) * staffing_pen
        discharge_utc = admit_utc + timedelta(days=los_days)
        self._ward_release[ward].append(discharge_utc)

        icu_admit = icu_release = None
        if icu:
            icu_admit = admit_utc
            icu_days = max(0.4, min(los_days * rng.uniform(0.4, 0.9), rng.gauss(3.0, 1.5)))
            icu_release = admit_utc + timedelta(days=icu_days)

        prov = rng.choice(self._providers_by_specialty.get(sl.specialty) or self.result.providers)
        stay = InpatientStay(pt.ref, sl_key, source, ward, admit_utc, discharge_utc, icu,
                             icu_admit, icu_release, prov.ref, round(boarding_min, 1),
                             list(seed_orders or []))

        ct_down_days = {i for d in disruptions if d.kind == "modality_down" and d.target == "CT"
                        for i in d.day_index}
        drug_out = set()
        for d in disruptions:
            if d.kind == "drug_stockout":
                drug_out.update(d.target.split(","))

        n_days = max(1, int(round(los_days)))
        for dd in range(n_days):
            t0 = admit_utc + timedelta(days=dd, hours=rng.uniform(5, 9))
            if t0 >= discharge_utc:
                break
            ct_down = (di + dd) in ct_down_days
            for code in rng.sample(list(sl.lab_codes), min(rng.randint(1, 3), len(sl.lab_codes))):
                stay.orders.append(self._make_order(rng, "lab", code, t0, dd == 0 and icu,
                                                    "inpatient", sl_key, ct_down, drug_out))
            if rng.random() < (0.5 if dd == 0 else 0.15):
                stay.orders.append(self._make_order(rng, "imaging", rng.choice(sl.img_codes),
                                                    t0, False, "inpatient", sl_key, ct_down, drug_out))
            for code in rng.sample(list(sl.rx_codes), min(rng.randint(1, 3), len(sl.rx_codes))):
                stay.orders.append(self._make_order(rng, "medication", code, t0, False,
                                                    "inpatient", sl_key, ct_down, drug_out))
        self.result.stays.append(stay)
