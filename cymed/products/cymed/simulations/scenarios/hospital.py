"""
"Cymed US Specialty Hospital" (Amman, Jordan) + a 5-clinic network.

Data only. The engine turns this into a 7-day operational flow: emergency
arrivals -> triage -> disposition; outpatient clinic sessions; direct and ED
admissions -> bed assignment -> (ICU) -> discharge; and lab / imaging /
pharmacy orders with realistic turnaround.

"Condition streams" (OB, cardiology, orthopedics, neonatal, ...) are modelled
as `SERVICE_LINES`: each carries its own share of clinic and ED demand, admit
rate, length of stay, ICU rate and order profile, so the one ADT / encounter /
order machinery produces all of them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CITY = "Amman"
TIMEZONE = "Asia/Amman"
COUNTRY = "JO"

HOSPITAL = {
    "name": "Cymed US Specialty Hospital",
    "code": "CUSH-AMM",
}

# ward code -> (display, room_type, bed_count)
WARDS: dict[str, tuple[str, str, int]] = {
    "ED": ("Emergency Department", "exam", 22),
    "ICU": ("Intensive Care Unit", "icu", 18),
    "CCU": ("Cardiac Care Unit", "icu", 14),
    "MS": ("Medical-Surgical", "standard", 70),
    "ORTHO": ("Orthopedic Ward", "standard", 26),
    "OB": ("Maternity Ward", "standard", 28),
    "PEDS": ("Pediatric Ward", "standard", 14),
    "NICU": ("Neonatal ICU", "icu", 12),
    "OR": ("Operating Rooms", "operating", 6),
    "PACU": ("Recovery / PACU", "recovery", 8),
}

# clinic code -> (display, specialty_code, rooms, slots_per_provider_day)
CLINICS: dict[str, tuple[str, str, int, int]] = {
    "CL-CARD": ("Cymed Cardiology Clinic", "cardiology", 6, 16),
    "CL-ORTHO": ("Cymed Orthopedics Clinic", "orthopedics", 6, 18),
    "CL-WH": ("Cymed Women's Health Clinic", "obgyn", 5, 16),
    "CL-PEDS": ("Cymed Pediatrics Clinic", "pediatrics", 5, 20),
    "CL-FM": ("Cymed Family Medicine Clinic", "family_medicine", 8, 22),
}

# specialty_code -> (display, physician_count, nurse_count)
SPECIALTIES: dict[str, tuple[str, int, int]] = {
    "cardiology": ("Cardiology", 6, 10),
    "orthopedics": ("Orthopedics", 5, 8),
    "obgyn": ("Obstetrics & Gynecology", 6, 14),
    "pediatrics": ("Pediatrics", 5, 10),
    "neonatology": ("Neonatology", 3, 12),
    "internal_medicine": ("Internal Medicine", 8, 16),
    "emergency_medicine": ("Emergency Medicine", 9, 24),
    "radiology": ("Radiology", 5, 6),
    "pathology": ("Pathology", 3, 5),
    "anesthesiology": ("Anesthesiology", 4, 6),
    "general_surgery": ("General Surgery", 5, 8),
    "family_medicine": ("Family Medicine", 6, 8),
}

# ---------------------------------------------------------------------------
# Order catalogue.  turnaround = (routine_minutes, stat_minutes).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LabTest:
    code: str
    name: str
    turnaround: tuple[int, int]
    cost: float


@dataclass(frozen=True)
class ImagingStudy:
    code: str
    name: str
    modality: str
    turnaround: tuple[int, int]
    cost: float


@dataclass(frozen=True)
class Medication:
    code: str
    name: str
    turnaround: tuple[int, int]     # order -> administered / dispensed
    cost: float


LAB_TESTS: tuple[LabTest, ...] = (
    LabTest("LB-CBC", "Complete Blood Count", (55, 25), 8.0),
    LabTest("LB-BMP", "Basic Metabolic Panel", (60, 30), 9.0),
    LabTest("LB-TROP", "Troponin I", (50, 22), 14.0),
    LabTest("LB-COAG", "Coagulation (PT/INR/aPTT)", (65, 30), 11.0),
    LabTest("LB-LFT", "Liver Function Tests", (70, 35), 10.0),
    LabTest("LB-HBA1C", "HbA1c", (120, 120), 12.0),
    LabTest("LB-BC", "Blood Culture", (2880, 2880), 22.0),
    LabTest("LB-UA", "Urinalysis", (45, 20), 6.0),
    LabTest("LB-TS", "Type & Screen", (60, 40), 18.0),
    LabTest("LB-BNP", "BNP", (60, 30), 16.0),
    LabTest("LB-LACT", "Lactate", (35, 15), 9.0),
)

IMAGING_STUDIES: tuple[ImagingStudy, ...] = (
    ImagingStudy("IM-CXR", "Chest X-ray", "XR", (90, 30), 35.0),
    ImagingStudy("IM-XR-LIMB", "Limb X-ray", "XR", (80, 30), 33.0),
    ImagingStudy("IM-CT-HEAD", "CT Head without contrast", "CT", (120, 40), 180.0),
    ImagingStudy("IM-CT-CHEST", "CT Chest with contrast", "CT", (150, 55), 220.0),
    ImagingStudy("IM-CT-ABD", "CT Abdomen/Pelvis", "CT", (150, 60), 240.0),
    ImagingStudy("IM-MRI-BRAIN", "MRI Brain", "MRI", (300, 120), 420.0),
    ImagingStudy("IM-MRI-KNEE", "MRI Knee", "MRI", (320, 180), 390.0),
    ImagingStudy("IM-US-OB", "Obstetric Ultrasound", "US", (110, 45), 90.0),
    ImagingStudy("IM-ECHO", "Echocardiogram", "US", (180, 60), 160.0),
)

MEDICATIONS: tuple[Medication, ...] = (
    Medication("RX-ASA", "Aspirin 81mg", (40, 15), 1.5),
    Medication("RX-HEP", "Heparin infusion", (45, 15), 12.0),
    Medication("RX-CEFTRI", "Ceftriaxone 1g IV", (55, 20), 9.0),
    Medication("RX-MORPH", "Morphine 4mg IV", (35, 12), 4.0),
    Medication("RX-ONDAN", "Ondansetron 4mg IV", (35, 15), 3.0),
    Medication("RX-INSULIN", "Insulin sliding scale", (50, 20), 6.0),
    Medication("RX-OXY", "Oxytocin infusion", (40, 15), 8.0),
    Medication("RX-KETO", "Ketorolac 30mg IV", (40, 15), 3.5),
    Medication("RX-ENOX", "Enoxaparin 40mg SC", (60, 30), 7.0),
    Medication("RX-PARA", "Paracetamol 1g IV", (35, 15), 2.5),
)

LAB_BY_CODE = {t.code: t for t in LAB_TESTS}
IMG_BY_CODE = {s.code: s for s in IMAGING_STUDIES}
RX_BY_CODE = {m.code: m for m in MEDICATIONS}

# ---------------------------------------------------------------------------
# Service lines ("condition streams")
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ServiceLine:
    key: str
    display: str
    specialty: str
    ward: str                      # inpatient ward for admissions
    clinic: str
    clinic_share: float            # share of outpatient demand
    ed_share: float                # share of ED demand
    admit_rate: float              # P(admit | ED visit)
    direct_admits_per_day: float
    alos_days: tuple[float, float]  # (mean, sd)
    icu_rate: float                # P(ICU | admitted)
    lab_codes: tuple[str, ...]
    img_codes: tuple[str, ...]
    rx_codes: tuple[str, ...]
    icd: str
    complaint: str


SERVICE_LINES: tuple[ServiceLine, ...] = (
    ServiceLine("cardiac", "Cardiac", "cardiology", "CCU", "CL-CARD",
                clinic_share=0.22, ed_share=0.20, admit_rate=0.42,
                direct_admits_per_day=2.5, alos_days=(4.2, 2.0), icu_rate=0.35,
                lab_codes=("LB-TROP", "LB-CBC", "LB-BMP", "LB-BNP", "LB-COAG"),
                img_codes=("IM-CXR", "IM-ECHO", "IM-CT-CHEST"),
                rx_codes=("RX-ASA", "RX-HEP", "RX-ENOX", "RX-MORPH"),
                icd="BA40", complaint="Chest pain / palpitations"),
    ServiceLine("ortho", "Orthopedic", "orthopedics", "ORTHO", "CL-ORTHO",
                clinic_share=0.20, ed_share=0.18, admit_rate=0.30,
                direct_admits_per_day=1.8, alos_days=(3.1, 1.6), icu_rate=0.05,
                lab_codes=("LB-CBC", "LB-BMP", "LB-COAG", "LB-TS"),
                img_codes=("IM-XR-LIMB", "IM-CT-ABD", "IM-MRI-KNEE"),
                rx_codes=("RX-KETO", "RX-MORPH", "RX-ENOX", "RX-PARA"),
                icd="FB80", complaint="Limb injury / joint pain"),
    ServiceLine("obstetric", "Obstetric", "obgyn", "OB", "CL-WH",
                clinic_share=0.20, ed_share=0.12, admit_rate=0.55,
                direct_admits_per_day=4.0, alos_days=(2.4, 1.1), icu_rate=0.03,
                lab_codes=("LB-CBC", "LB-BMP", "LB-UA", "LB-TS"),
                img_codes=("IM-US-OB",),
                rx_codes=("RX-OXY", "RX-PARA", "RX-ONDAN"),
                icd="JA00", complaint="Labour / pregnancy concern"),
    ServiceLine("neonatal", "Neonatal", "neonatology", "NICU", "CL-PEDS",
                clinic_share=0.04, ed_share=0.03, admit_rate=0.70,
                direct_admits_per_day=1.4, alos_days=(6.5, 4.0), icu_rate=0.80,
                lab_codes=("LB-CBC", "LB-BMP", "LB-BC"),
                img_codes=("IM-CXR",),
                rx_codes=("RX-CEFTRI", "RX-PARA"),
                icd="KA00", complaint="Neonatal — prematurity / distress"),
    ServiceLine("pediatric", "Pediatric", "pediatrics", "PEDS", "CL-PEDS",
                clinic_share=0.14, ed_share=0.17, admit_rate=0.18,
                direct_admits_per_day=1.0, alos_days=(2.2, 1.0), icu_rate=0.06,
                lab_codes=("LB-CBC", "LB-BMP", "LB-UA", "LB-BC"),
                img_codes=("IM-CXR", "IM-XR-LIMB"),
                rx_codes=("RX-CEFTRI", "RX-ONDAN", "RX-PARA"),
                icd="1A00", complaint="Fever / vomiting / cough"),
    ServiceLine("general", "General Medical", "internal_medicine", "MS", "CL-FM",
                clinic_share=0.20, ed_share=0.30, admit_rate=0.26,
                direct_admits_per_day=3.0, alos_days=(3.8, 2.2), icu_rate=0.12,
                lab_codes=("LB-CBC", "LB-BMP", "LB-LFT", "LB-HBA1C", "LB-UA", "LB-LACT"),
                img_codes=("IM-CXR", "IM-CT-HEAD", "IM-CT-ABD"),
                rx_codes=("RX-CEFTRI", "RX-INSULIN", "RX-ENOX", "RX-PARA", "RX-ONDAN"),
                icd="1B10", complaint="Fever / dyspnea / abdominal pain"),
)
SL_BY_KEY = {s.key: s for s in SERVICE_LINES}

# ---------------------------------------------------------------------------
# Demand
# ---------------------------------------------------------------------------

ED_ARRIVALS_PER_DAY = 96
ED_WEEKDAY_FACTOR = {0: 1.10, 1: 1.00, 2: 0.98, 3: 0.97, 4: 1.02, 5: 1.12, 6: 1.14}
ED_HOURLY_WEIGHTS = {
    0: 1.2, 1: 0.9, 2: 0.7, 3: 0.6, 4: 0.6, 5: 0.8, 6: 1.1, 7: 1.6, 8: 2.4,
    9: 3.1, 10: 3.6, 11: 3.8, 12: 3.6, 13: 3.3, 14: 3.1, 15: 3.0, 16: 3.1,
    17: 3.2, 18: 3.4, 19: 3.3, 20: 2.9, 21: 2.4, 22: 1.9, 23: 1.5,
}
ED_ARRIVAL_METHODS = {"walk-in": 0.62, "ambulance": 0.30, "police": 0.04, "referral": 0.04}

# ESI mix by arrival method (1 = sickest)
ESI_MIX = {
    "ambulance": {1: 0.08, 2: 0.34, 3: 0.40, 4: 0.15, 5: 0.03},
    "walk-in": {1: 0.005, 2: 0.10, 3: 0.42, 4: 0.35, 5: 0.125},
    "police": {1: 0.02, 2: 0.20, 3: 0.45, 4: 0.28, 5: 0.05},
    "referral": {1: 0.03, 2: 0.30, 3: 0.47, 4: 0.17, 5: 0.03},
}

# door-to-provider target minutes and door-to-disposition target by ESI
ED_DISPO_TARGET_MIN = {1: 60, 2: 120, 3: 240, 4: 200, 5: 160}
LWBS_BASE_RATE = 0.018            # scales up with crowding

CLINIC_NOSHOW_RATE = 0.13
CLINIC_WALKIN_RATE = 0.10
CLINIC_SESSION_DAYS = {0, 1, 2, 3, 4, 6}   # closed Friday (5)
CLINIC_ORDER_RATE = 0.55          # P(visit generates >=1 order)

BED_CLEAN_TURNOVER_MIN = (45, 120)

# ---------------------------------------------------------------------------
# Scenario variants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Disruption:
    kind: str
    day_index: tuple[int, ...]
    magnitude: float = 1.0
    target: str = ""
    note: str = ""


VARIANTS: dict[str, dict] = {
    "baseline": {"label": "Baseline week", "disruptions": ()},
    "ed_surge": {
        "label": "Emergency surge — +60% ED arrivals on days 3-4 (mass casualty + heat wave)",
        "disruptions": (Disruption("ed_surge", (2, 3), magnitude=0.60,
                                   note="regional incident + seasonal spike"),),
    },
    "imaging_ct_downtime": {
        "label": "CT scanner down for 2 days (days 4-5) — imaging turnaround balloons",
        "disruptions": (Disruption("modality_down", (3, 4), target="CT",
                                   note="CT tube failure, engineer on the way"),),
    },
    "nurse_shortage": {
        "label": "Nursing shortage — Med-Surg staffed 35% short on days 5-6 (boarding, longer stays)",
        "disruptions": (Disruption("ward_staffing", (4, 5), magnitude=0.35, target="MS",
                                   note="sick calls + agency gap"),),
    },
    "pharmacy_stockout": {
        "label": "Pharmacy stockout — ceftriaxone + heparin unavailable days 2-3",
        "disruptions": (Disruption("drug_stockout", (1, 2), target="RX-CEFTRI,RX-HEP",
                                   note="wholesaler backorder"),),
    },
}


def variant(name: str) -> dict:
    if name not in VARIANTS:
        raise KeyError(f"unknown hospital scenario '{name}'; choose from {sorted(VARIANTS)}")
    return VARIANTS[name]
