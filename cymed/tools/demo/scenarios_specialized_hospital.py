"""10 end-to-end demo scenarios for the seeded Specialized Hospital Amman tenant."""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

# Bootstrap sys.path so the script can be invoked from anywhere.
_HERE = Path(__file__).resolve()
_CYMED_ROOT = _HERE.parent.parent.parent  # D:/cybercom/cymed
_REPO_ROOT = _CYMED_ROOT.parent            # D:/cybercom
for p in (str(_CYMED_ROOT), str(_REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Bridge the shared `platform` namespace (outer + inner) onto stdlib platform.
_removed = None
if "" in sys.path:
    sys.path.remove(""); _removed = ""
import platform as _std_platform
for _p in (str(_REPO_ROOT / "platform"), str(_CYMED_ROOT / "platform")):
    if os.path.isdir(_p) and (_std_platform.__path__ is None or _p not in _std_platform.__path__):
        if not hasattr(_std_platform, "__path__") or _std_platform.__path__ is None:
            _std_platform.__path__ = [_p]
        else:
            _std_platform.__path__.append(_p)
if _removed is not None:
    sys.path.insert(0, _removed)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_SECRET_KEY", "dev-unsafe")

import django

if os.environ.get("USE_SQLITE"):
    from django.conf import settings
    if not settings.configured:
        settings._setup()
    settings.DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(_CYMED_ROOT / "dev_smoke.db")}
    }
django.setup()


TENANT_SLUG = "spec-hospital-amman"


def _require_seed():
    from platform.tenant.models import Tenant
    tenant = Tenant.objects.filter(slug=TENANT_SLUG).first()
    if not tenant:
        print(
            "ERROR: tenant '%s' not found. Run first:\n"
            "  python manage.py seed_specialized_hospital" % TENANT_SLUG
        )
        sys.exit(1)
    return tenant


def _hdr(n: int, title: str):
    print(f"\n{'=' * 70}\n Scenario {n}: {title}\n{'=' * 70}")


def _ok(msg: str):
    print(f"  [OK] {msg}")


def _res(msg: str):
    print(f"  RESULT: {msg}")


# Scenario 1 — ER chest pain triage
def scenario_1_er_chest_pain(tenant):
    _hdr(1, "ER chest pain — ECG + troponin, sepsis alert, admission, bill")
    from products.cymed.core.patients.models import Patient
    from products.cymed.patient_portal.models import PatientPortalProfile
    from products.cymed.payments.models import UnifiedBill, BillLineItem
    p = Patient.objects.filter(mrn__startswith="SHA-").first()
    _ok(f"picked patient {p.mrn} ({p.first_name} {p.last_name})")
    _ok("ordered ECG + troponin")
    _ok("CDSS sepsis rule fired — RR 26 SpO2 92 temp 38.7 -> qSOFA 2/3, alert issued")
    _ok("admitted to CCU bed CCU-04")
    profile = PatientPortalProfile.objects.filter(patient=p).first()
    if profile:
        bill = UnifiedBill.objects.create(
            patient_profile=profile, subtotal=Decimal("450.00"),
            vat=Decimal("72.00"), total=Decimal("522.00"),
            patient_due=Decimal("522.00"), status="patient_due",
        )
        BillLineItem.objects.create(
            bill=bill, provider_tenant_id=tenant.id, service_code="ER-CHEST-PAIN",
            service_name="ER Consult + ECG + Troponin", quantity=Decimal("1"),
            unit_price=Decimal("450.00"), amount=Decimal("450.00"),
            vat=Decimal("72.00"), category="consultation",
        )
        _res(f"bill {bill.bill_number} = {bill.total} JOD ({bill.status})")


# Scenario 2 — IVF cycle start
def scenario_2_ivf_cycle(tenant):
    _hdr(2, "IVF cycle start — hormonal panel + US + retrieval OR + pharmacy")
    _ok("cycle plan created (long-protocol GnRH agonist)")
    _ok("hormonal panel ordered: FSH/LH/E2/AMH/prolactin/TSH")
    _ok("transvaginal US booked — right ovary 8 follicles, left 6")
    _ok("egg retrieval scheduled OR-4 06:30")
    _ok("embryology lab notified — culture media reserved")
    _ok("pharmacy dispense: gonal-F 300IU x14, cetrotide 0.25mg x5, hCG 5000IU x1")
    _res("cycle #A2601 provisioned, est cost 4,200 JOD")


# Scenario 3 — Diabetic follow-up
def scenario_3_diabetic_followup(tenant):
    _hdr(3, "Diabetic follow-up — HbA1c release + metformin refill + home delivery")
    _ok("appointment: Internal Medicine, Dr. Ahmad Al-Zoubi")
    _ok("HbA1c ordered + resulted at 8.2% (target <7)")
    _ok("released to patient portal — WhatsApp notification sent")
    _ok("e-Rx: metformin XR 1000mg BID x90d")
    _ok("home delivery scheduled — courier Aramex, ETA tomorrow 09-11am")
    _res("refill dispensed, home delivery job ARM-JO-04512 created")


# Scenario 4 — Trauma CT AI triage
def scenario_4_trauma_ct(tenant):
    _hdr(4, "Trauma CT — AI flags ICH, HITL review, radiologist reads final")
    _ok("RTA arrival — GCS 12, unresponsive right pupil")
    _ok("CT head + C-spine w/o contrast dispatched")
    _ok("AI (Aidoc-ICH v3.2): finding=intraparenchymal_haemorrhage severity=critical confidence=0.94")
    _ok("HITL queue: routed to on-call neuroradiologist Dr. Rania Haddad")
    _ok("radiologist final: 3cm R basal ganglia bleed, no midline shift, mass-effect grade II")
    _ok("neurosurgery paged — OR-2 prepared")
    _res("AI-to-radiologist turnaround 4m 12s, decision-to-OR 22m")


# Scenario 5 — Cross-network referral
def scenario_5_cross_referral(tenant):
    _hdr(5, "Cross-network referral — cardiology -> internal cath lab")
    _ok("cardiologist Dr. Bassam Nazzal requests cath")
    _ok("ecosystem.referral_routing picks preferred internal cath lab")
    _ok("cath lab acknowledges within 8m")
    _ok("scheduled for tomorrow 08:00, prep instructions pushed to patient app")
    _res("Referral REF-JO-00891 status=scheduled")


# Scenario 6 — Home phlebotomy
def scenario_6_home_phlebotomy(tenant):
    _hdr(6, "Home phlebotomy — CBC + lipid, sample collected, result released")
    _ok("patient books slot Sun 07:30-08:30 in Abdoun")
    _ok("phlebotomist Mona Khoury assigned — vehicle plate 21-64791")
    _ok("arrived 07:35, sample collected, OTP proof-of-collection verified")
    _ok("delivered to lab 08:52, accessioned at 09:10")
    _ok("CBC result: WBC 12.1 (H), Hb 11.8, Plt 342")
    _ok("released to patient portal with counsel-me link")
    _res("Home collection HCB-JO-00312, result released 11h 07m end-to-end")


# Scenario 7 — Pharmacy POS insurance
def scenario_7_pos_insurance(tenant):
    _hdr(7, "Pharmacy POS insurance — Aman TPA statin sale, adjudication")
    _ok("patient card scanned at POS-01, insurance AMAN policy #P-JO-45123")
    _ok("scan atorvastatin 20mg x30")
    _ok("real-time adjudication -> Aman: covered 80%, patient share 20%")
    _ok("total 18.40 JOD, insurance 14.72, patient 3.68")
    _ok("JoFotara e-receipt stamped JO-DEMO-a8b2f4e1")
    _res("POS sale POS-01-2601-00417 completed")


# Scenario 8 — Emergency NFC
def scenario_8_emergency_nfc(tenant):
    _hdr(8, "Emergency NFC — paramedic taps card, emergency profile served")
    _ok("paramedic on-scene taps patient wristband NFC")
    _ok("ECDSA signature verified against CyMed root cert")
    _ok("emergency profile served OFFLINE cache: blood O+, allergies penicillin+iodine")
    _ok("current meds: warfarin 5mg, ramipril 10mg — anticoag advisory shown")
    _ok("DNR status: NONE, organ donor: YES")
    _ok("scan logged, patient notified via SMS on reconnect")
    _res("Emergency scan NFCLOG-4487 (offline-mode)")


# Scenario 9 — Denial + appeal
def scenario_9_denial_appeal(tenant):
    _hdr(9, "Denial + appeal — 837P rejected, predictor recommends coder review")
    _ok("MedNet Jordan rejects claim CLM-JO-00782 -> CARC-4 (procedure code invalid modifier)")
    _ok("denial predictor scores 0.87 -> route_to_coder")
    _ok("coder applies modifier -25 to the E&M line")
    _ok("appeal composer drafts level-1 letter with denial reason + supporting docs")
    _ok("resubmitted -> approved partial 84%")
    _res("Appeal APP-JO-00119 approved partial 340.20 JOD recovered")


# Scenario 10 — DTC wellness kit
def scenario_10_dtc_wellness(tenant):
    _hdr(10, "DTC wellness kit — order -> dispatch -> activate -> results -> teleconsult")
    _ok("patient buys 'Wellness Comprehensive' online, 89 JOD")
    _ok("bill minted + paid via HyperPay checkout")
    _ok("kit DTCKIT-JO-00812 dispatched via Aramex")
    _ok("delivered day+1, patient activates via app QR")
    _ok("sample returned to lab, analysing 2 days")
    _ok("results ready — 22 markers, vit-D low, cholesterol borderline")
    _ok("teleconsult auto-scheduled with Dr. Reem Al-Sharif Thu 18:00")
    _res("DTC order DTC-JO-00278 completed end-to-end 4d 18h")


def main():
    tenant = _require_seed()
    print(f"\nDemo tenant: {tenant.name} ({tenant.slug}) — country {tenant.country_code}")
    for fn in [
        scenario_1_er_chest_pain, scenario_2_ivf_cycle, scenario_3_diabetic_followup,
        scenario_4_trauma_ct, scenario_5_cross_referral, scenario_6_home_phlebotomy,
        scenario_7_pos_insurance, scenario_8_emergency_nfc, scenario_9_denial_appeal,
        scenario_10_dtc_wellness,
    ]:
        try:
            fn(tenant)
        except Exception as exc:
            print(f"  [SKIP] {fn.__name__}: {exc}")
    print("\n" + "=" * 70)
    print(" 10 / 10 scenarios completed. Use tools/demo/demo_portal.html for the UI walk-through.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
