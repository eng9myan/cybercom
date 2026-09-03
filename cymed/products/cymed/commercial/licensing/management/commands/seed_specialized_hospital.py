"""Seed a complete demo tenant for Specialized Hospital Amman (Jordan)."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# --- Fallback name / reference pools (used if tools.demo.data.names_jo is not
# importable at command execution time). Kept intentionally small — the real
# module is much richer, but the seeder must not crash when the sibling data
# module is missing.
_FALLBACK_FIRST_M = ["Ahmad", "Mohammad", "Omar", "Yousef", "Khaled"]
_FALLBACK_FIRST_F = ["Fatima", "Sara", "Rania", "Mona", "Layla"]
_FALLBACK_LAST = ["Al-Zoubi", "Haddad", "Nazzal", "Khoury", "Al-Masri"]
_FALLBACK_SPECIALTIES = [
    "Cardiology", "Internal Medicine", "General Surgery", "Pediatrics",
    "Obstetrics & Gynecology", "Radiology", "Emergency Medicine",
]
_FALLBACK_CITIES = [
    "Amman", "Zarqa", "Irbid", "Aqaba", "Salt", "Madaba", "Karak", "Ma'an",
]
_FALLBACK_COMPLAINTS = [
    "الم في الصدر / Chest pain",
    "ضيق تنفس / Shortness of breath",
    "حمى / Fever",
    "الم في البطن / Abdominal pain",
    "صداع شديد / Severe headache",
]
_FALLBACK_INSURERS = [
    {"code": "AMAN", "name": "Aman Insurance"},
    {"code": "MEDNET_JO", "name": "MedNet Jordan"},
    {"code": "GLOBEMED_JO", "name": "GlobeMed Jordan"},
    {"code": "NEXTCARE_JO", "name": "Nextcare Jordan"},
    {"code": "NISR", "name": "Al-Nisr Al-Arabi"},
    {"code": "JORDAN_INS", "name": "Jordan Insurance"},
    {"code": "JERUSALEM_INS", "name": "Jerusalem Insurance"},
    {"code": "ISLAMIC_INS", "name": "Islamic Insurance"},
    {"code": "TRUST_INT", "name": "Trust International"},
    {"code": "FIRST_INS", "name": "First Insurance"},
    {"code": "RMS", "name": "Royal Medical Services"},
]
_FALLBACK_PHARMACY_OTC = [
    {"name": "Paracetamol 500mg", "price": Decimal("2.50")},
    {"name": "Ibuprofen 400mg", "price": Decimal("3.10")},
    {"name": "Loratadine 10mg", "price": Decimal("3.80")},
    {"name": "Vitamin D3 1000 IU", "price": Decimal("6.40")},
    {"name": "Omeprazole 20mg", "price": Decimal("5.20")},
]
_FALLBACK_PHARMACY_RX = [
    {"name": "Amoxicillin 500mg", "price": Decimal("5.60")},
    {"name": "Atorvastatin 20mg", "price": Decimal("9.20")},
    {"name": "Metformin 500mg", "price": Decimal("4.40")},
    {"name": "Losartan 50mg", "price": Decimal("8.40")},
    {"name": "Levothyroxine 50mcg", "price": Decimal("5.40")},
]


def _load_reference_data() -> dict:
    """Import the shared JO reference pack; fall back to inline stubs on failure."""
    try:
        from tools.demo.data import names_jo  # type: ignore

        return {
            "first_m": list(getattr(names_jo, "FIRST_NAMES_M", _FALLBACK_FIRST_M)),
            "first_f": list(getattr(names_jo, "FIRST_NAMES_F", _FALLBACK_FIRST_F)),
            "last": list(getattr(names_jo, "LAST_NAMES", _FALLBACK_LAST)),
            "specialties": list(
                getattr(names_jo, "SPECIALTIES", _FALLBACK_SPECIALTIES)
            ),
            "cities": list(getattr(names_jo, "CITIES", _FALLBACK_CITIES)),
            "complaints": list(
                getattr(names_jo, "CHIEF_COMPLAINTS", _FALLBACK_COMPLAINTS)
            ),
            "insurers": list(getattr(names_jo, "INSURERS_JO", _FALLBACK_INSURERS)),
            "otc": list(getattr(names_jo, "PHARMACY_OTC", _FALLBACK_PHARMACY_OTC)),
            "rx": list(getattr(names_jo, "PHARMACY_RX", _FALLBACK_PHARMACY_RX)),
        }
    except Exception:
        return {
            "first_m": _FALLBACK_FIRST_M,
            "first_f": _FALLBACK_FIRST_F,
            "last": _FALLBACK_LAST,
            "specialties": _FALLBACK_SPECIALTIES,
            "cities": _FALLBACK_CITIES,
            "complaints": _FALLBACK_COMPLAINTS,
            "insurers": _FALLBACK_INSURERS,
            "otc": _FALLBACK_PHARMACY_OTC,
            "rx": _FALLBACK_PHARMACY_RX,
        }


# Bookable imaging catalog — modality, code, name, base price (JOD).
_IMAGING_CATALOG = [
    ("xray", "Chest"), ("xray", "Abdomen"), ("xray", "Knee"), ("xray", "Spine"),
    ("xray", "Pelvis"), ("xray", "Hand"), ("xray", "Foot"), ("xray", "Skull"),
    ("ct", "Brain"), ("ct", "Chest"), ("ct", "Abdomen"), ("ct", "Pelvis"),
    ("ct", "Angiography Coronary"), ("ct", "Sinus"),
    ("mri", "Brain"), ("mri", "Cervical Spine"), ("mri", "Lumbar Spine"),
    ("mri", "Knee"), ("mri", "Shoulder"), ("mri", "Cardiac"),
    ("us", "Abdomen"), ("us", "Pelvis"), ("us", "Obstetric"),
    ("us", "Thyroid"), ("us", "Breast"), ("us", "Doppler Carotid"),
    ("mammo", "Screening"), ("mammo", "Diagnostic"),
    ("dexa", "Bone Density"),
    ("nucmed", "Bone Scan"), ("nucmed", "MUGA"),
    ("pet", "FDG Whole Body"), ("pet", "Cardiac Viability"),
    ("fluoro", "Barium Swallow"), ("fluoro", "Angiography Coronary"),
    ("fluoro", "Angiography Cerebral"),
    ("dental", "Panoramic OPG"), ("dental", "Cephalometric"),
    ("us", "Echocardiogram"), ("ct", "PET-CT Oncology"),
]

# Bookable lab catalog — category, code, name, base price (JOD).
_LAB_CATALOG = [
    ("hematology", "CBC", "Complete Blood Count"),
    ("hematology", "ESR", "Erythrocyte Sedimentation Rate"),
    ("hematology", "PT_INR", "Prothrombin Time / INR"),
    ("hematology", "APTT", "Activated Partial Thromboplastin Time"),
    ("hematology", "D_DIMER", "D-Dimer"),
    ("hematology", "FIBRINOGEN", "Fibrinogen"),
    ("chemistry", "CMP", "Comprehensive Metabolic Panel"),
    ("chemistry", "BMP", "Basic Metabolic Panel"),
    ("chemistry", "GLUC_FBS", "Fasting Blood Glucose"),
    ("chemistry", "GLUC_RBS", "Random Blood Glucose"),
    ("chemistry", "HBA1C", "Glycated Hemoglobin HbA1c"),
    ("chemistry", "LIPID", "Lipid Panel"),
    ("chemistry", "LFT", "Liver Function Tests"),
    ("chemistry", "RFT", "Renal Function Tests"),
    ("chemistry", "URIC", "Uric Acid"),
    ("chemistry", "AMYLASE", "Serum Amylase"),
    ("chemistry", "LIPASE", "Serum Lipase"),
    ("chemistry", "CRP", "C-Reactive Protein"),
    ("chemistry", "PROCAL", "Procalcitonin"),
    ("endocrine", "TSH", "Thyroid Stimulating Hormone"),
    ("endocrine", "T3_FREE", "Free T3"),
    ("endocrine", "T4_FREE", "Free T4"),
    ("endocrine", "CORTISOL_AM", "Cortisol AM"),
    ("endocrine", "PROLACTIN", "Prolactin"),
    ("endocrine", "TESTOSTERONE", "Total Testosterone"),
    ("endocrine", "ESTRADIOL", "Estradiol"),
    ("endocrine", "PROGESTERONE", "Progesterone"),
    ("endocrine", "FSH", "Follicle Stimulating Hormone"),
    ("endocrine", "LH", "Luteinizing Hormone"),
    ("endocrine", "INSULIN", "Insulin"),
    ("vitamins", "VITD", "Vitamin D 25-OH"),
    ("vitamins", "VITB12", "Vitamin B12"),
    ("vitamins", "FOLATE", "Folate"),
    ("vitamins", "FERRITIN", "Ferritin"),
    ("vitamins", "IRON_TIBC", "Iron / TIBC"),
    ("cardiac", "TROP_I", "Troponin I High Sensitivity"),
    ("cardiac", "CKMB", "CK-MB"),
    ("cardiac", "BNP", "BNP"),
    ("cardiac", "NT_PROBNP", "NT-proBNP"),
    ("tumor_markers", "PSA", "Prostate Specific Antigen"),
    ("tumor_markers", "CA125", "CA 125"),
    ("tumor_markers", "CA153", "CA 15-3"),
    ("tumor_markers", "CA199", "CA 19-9"),
    ("tumor_markers", "CEA", "Carcinoembryonic Antigen"),
    ("tumor_markers", "AFP", "Alpha Fetoprotein"),
    ("serology", "HBSAG", "Hepatitis B Surface Antigen"),
    ("serology", "ANTI_HCV", "Anti-Hepatitis C"),
    ("serology", "ANTI_HIV", "HIV Antibody"),
    ("serology", "VDRL", "VDRL Syphilis"),
    ("serology", "COVID_PCR", "SARS-CoV-2 PCR"),
    ("serology", "INFLU_PCR", "Influenza A/B PCR"),
    ("reproductive", "BETA_HCG", "Beta hCG Quantitative"),
    ("urine", "UA", "Urinalysis"),
    ("urine", "URINE_CULTURE", "Urine Culture and Sensitivity"),
    ("urine", "MICRO_ALB", "Microalbumin / Creatinine Ratio"),
    ("stool", "STOOL_OB", "Stool Occult Blood"),
    ("stool", "STOOL_CULTURE", "Stool Culture"),
    ("stool", "H_PYLORI", "H. pylori Stool Antigen"),
    ("micro", "BLOOD_CULTURE", "Blood Culture Aerobic"),
    ("micro", "SPUTUM_CULTURE", "Sputum Culture"),
]

_LAB_PACKAGES = [
    ("PKG_EXEC_M", "Executive Health — Male"),
    ("PKG_EXEC_F", "Executive Health — Female"),
    ("PKG_DM_MON", "Diabetes Monitoring"),
    ("PKG_HTN_MON", "Hypertension Monitoring"),
    ("PKG_CARDIAC", "Cardiac Risk"),
    ("PKG_THYROID", "Thyroid Full Screen"),
    ("PKG_PRECON_F", "Pre-conception — Female"),
    ("PKG_ANEMIA", "Anemia Workup"),
    ("PKG_PRE_OP", "Pre-Operative Basic"),
    ("PKG_HEP_SCREEN", "Hepatitis Screen"),
    ("PKG_STD_SCREEN", "STD Screen"),
    ("PKG_KIDNEY", "Kidney Function"),
    ("PKG_LIVER", "Liver Function"),
    ("PKG_PROSTATE", "Prostate Screening"),
    ("PKG_ONCO_F", "Women's Oncology Screen"),
]

_DTC_PRODUCTS = [
    ("WELL_START", "Wellness Starter Panel"),
    ("WELL_PLUS", "Wellness Plus Panel"),
    ("VITAMIN_FULL", "Vitamin & Mineral Complete"),
    ("HORMONE_F", "Female Hormone Panel"),
    ("HORMONE_M", "Male Hormone Panel"),
    ("STRESS_CORT", "Stress & Cortisol Kit"),
    ("SLEEP_KIT", "Sleep Quality Kit"),
    ("METABOLIC", "Metabolic Health Kit"),
    ("HEART_RISK", "Heart Risk Kit"),
    ("FERTILITY_F", "Fertility — Female"),
    ("FERTILITY_M", "Fertility — Male"),
    ("MICROBIOME", "Gut Microbiome Kit"),
    ("ALLERGY_FOOD", "Food Allergy Panel"),
    ("ALLERGY_ENV", "Environmental Allergy Panel"),
    ("GENETIC_PHARMA", "Pharmacogenomic Kit"),
    ("NUTRIGENOMIC", "Nutrigenomic Kit"),
    ("LONGEVITY", "Longevity & Biological Age"),
    ("VITAMIN_D", "Vitamin D Kit"),
    ("THYROID_HOME", "Thyroid Home Kit"),
    ("DIABETES_HOME", "Diabetes Home Kit"),
]


class Command(BaseCommand):
    """Provision a full demo tenant for Specialized Hospital Amman."""

    help = "Seed a complete demo tenant for Specialized Hospital Amman (Jordan)."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--tenant-slug", default="spec-hospital-amman")
        parser.add_argument("--patient-count", type=int, default=200)
        parser.add_argument("--encounter-count", type=int, default=300)

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def handle(self, *args, **opts):
        random.seed(42)
        self._ref = _load_reference_data()
        self._summary: dict = {
            "facilities": 0,
            "practitioners": 0,
            "patients": 0,
            "encounters": 0,
            "total_billed": Decimal("0"),
            "total_paid": Decimal("0"),
            "first_mrns": [],
            "sample_booking_ref": "",
        }

        if opts["wipe"]:
            self._wipe(opts["tenant_slug"])

        tenant_id, org_id = self._seed_tenant(opts["tenant_slug"])
        self._seed_facility(tenant_id, org_id)
        self._seed_practitioners(tenant_id)
        patient_ids, profile_ids = self._seed_patients(
            tenant_id, opts["patient_count"]
        )
        self._seed_insurers(tenant_id, profile_ids)
        self._seed_catalog(tenant_id)
        encounter_ids = self._seed_encounters(
            tenant_id, org_id, patient_ids, opts["encounter_count"]
        )
        self._seed_referrals_and_extras(tenant_id, profile_ids)
        self._seed_bills_and_claims(tenant_id, encounter_ids, profile_ids)
        self._print_summary(tenant_id)

    # ------------------------------------------------------------------
    # Wipe
    # ------------------------------------------------------------------

    def _wipe(self, slug: str) -> None:
        from platform.tenant.models import Tenant

        Tenant.objects.filter(slug=slug).delete()

    # ------------------------------------------------------------------
    # A) Tenant
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_tenant(self, slug: str) -> tuple[uuid.UUID, uuid.UUID]:
        from platform.tenant.models import (
            SubscriptionPlan,
            Tenant,
            TenantBranding,
            TenantConfiguration,
            TenantProfile,
            TenantStatus,
            TenantSubscription,
            TenantType,
        )
        from products.cymed.core.organizations.models import (
            Organization,
            OrganizationAccreditation,
            OrganizationAddress,
            OrganizationContact,
            OrganizationType,
        )

        tenant, _created = Tenant.objects.update_or_create(
            slug=slug,
            defaults={
                "name": "Specialized Hospital Amman",
                "display_name": "Specialized Hospital Amman",
                "tenant_type": TenantType.DEDICATED,
                "status": TenantStatus.ACTIVE,
                "country_code": "JO",
                "timezone": "Asia/Amman",
                "locale": "ar",
                "home_region": "me-central-1",
                "activated_at": timezone.now(),
                "metadata": {
                    "city": "Amman",
                    "district": "Al-Shmesani",
                    "currency": "JOD",
                    "founded_year": 1990,
                    "opened_year": 1993,
                    "beds": 265,
                    "operating_rooms": 21,
                    "specialties_count": 30,
                    "consultants_count": 750,
                    "nicu_incubators": 28,
                    "jci_cycles": [2008, 2011, 2014, 2017, 2020, 2023],
                    "cardiac_ccpc": True,
                },
            },
        )

        TenantProfile.objects.update_or_create(
            tenant=tenant,
            defaults={
                "legal_name": "Specialized Hospital Amman Co.",
                "contact_name": "CMO — Specialized Hospital Amman",
                "contact_email": "demo@spec-hospital-amman.jo",
                "contact_phone": "+96265001000",
                "billing_email": "billing@spec-hospital-amman.jo",
                "billing_address": "Al-Shmesani, Amman, Jordan",
                "industry": "Healthcare — Tertiary Hospital",
                "employee_count": 2200,
                "website": "https://www.specialty-hospital.com",
            },
        )
        TenantConfiguration.objects.update_or_create(
            tenant=tenant,
            defaults={
                "max_users": 3000,
                "max_api_calls_per_day": 500_000,
                "max_storage_gb": 2000,
                "data_residency_region": "me-central-1",
                "data_residency_country": "JO",
                "mfa_required": True,
                "audit_retention_days": 365,
            },
        )
        TenantBranding.objects.update_or_create(
            tenant=tenant,
            defaults={
                "primary_color": "#0A3D62",
                "secondary_color": "#3C6382",
                "accent_color": "#60A3BC",
                "app_name": "Specialized Hospital Amman",
                "tagline": "Excellence in cardiac & specialty care",
                "theme": "light",
                "rtl_default": True,
                "default_language": "ar",
                "supported_languages": ["ar", "en"],
            },
        )
        TenantSubscription.objects.update_or_create(
            tenant=tenant,
            plan=SubscriptionPlan.ENTERPRISE,
            defaults={
                "is_active": True,
                "monthly_price_usd": Decimal("18500.00"),
                "annual_price_usd": Decimal("199800.00"),
                "currency": "JOD",
                "auto_renew": True,
                "notes": "Demo tenant — CyMed Enterprise Hospital pack, JCI-ready.",
            },
        )

        org, _org_created = Organization.objects.update_or_create(
            slug=slug,
            defaults={
                "tenant_id": tenant.id,
                "name": "Specialized Hospital Amman",
                "organization_type": OrganizationType.HOSPITAL,
                "is_active": True,
            },
        )
        # Refresh tenant_id on repeat runs (update_or_create keeps it consistent
        # but writes only on create).
        if org.tenant_id != tenant.id:
            org.tenant_id = tenant.id
            org.save(update_fields=["tenant_id", "updated_at"])

        OrganizationAddress.objects.get_or_create(
            organization=org,
            line1="Queen Noor Street, Al-Shmesani",
            defaults={
                "tenant_id": tenant.id,
                "city": "Amman",
                "state": "Amman Governorate",
                "postal_code": "11194",
                "country": "Jordan",
            },
        )
        for system_val, val in (
            ("phone", "+96265001000"),
            ("fax", "+96265001099"),
            ("email", "info@spec-hospital-amman.jo"),
            ("url", "https://www.specialty-hospital.com"),
        ):
            OrganizationContact.objects.get_or_create(
                organization=org,
                telecom_system=system_val,
                telecom_value=val,
                defaults={"tenant_id": tenant.id},
            )
        for year in (2008, 2011, 2014, 2017, 2020, 2023):
            OrganizationAccreditation.objects.get_or_create(
                organization=org,
                accreditation_body="JCI",
                accreditation_number=f"JCI-CYCLE-{year}",
                defaults={
                    "tenant_id": tenant.id,
                    "valid_until": date(year + 3, 12, 31),
                },
            )
        OrganizationAccreditation.objects.get_or_create(
            organization=org,
            accreditation_body="JCI CCPC",
            accreditation_number="JCI-CCPC-AMI-HF-2023",
            defaults={"tenant_id": tenant.id, "valid_until": date(2026, 12, 31)},
        )

        return tenant.id, org.id

    # ------------------------------------------------------------------
    # B) Facilities
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_facility(self, tenant_id: uuid.UUID, org_id: uuid.UUID) -> None:
        from products.cymed.core.facilities.models import (
            Bed,
            Building,
            Department,
            Facility,
            Room,
            Ward,
        )

        facilities_spec = [
            ("SHA-MAIN", "Main Hospital — Al-Shmesani"),
            ("SHA-OPC", "Outpatient Clinic Tower"),
            ("SHA-IVF", "IVF & Reproductive Medicine Center"),
            ("SHA-CATH", "Cardiac Catheterization Laboratory"),
            ("SHA-IMG", "Imaging & Diagnostic Center"),
            ("SHA-LAB", "Main Clinical Laboratory"),
            ("SHA-PHARM", "Retail Pharmacy — Al-Shmesani"),
            ("SHA-HOME", "Home Healthcare Hub"),
        ]
        facilities: list = []
        for code, name in facilities_spec:
            fac, _ = Facility.objects.update_or_create(
                code=code,
                defaults={
                    "tenant_id": tenant_id,
                    "organization_id": org_id,
                    "name": name,
                    "is_active": True,
                },
            )
            if fac.tenant_id != tenant_id:
                fac.tenant_id = tenant_id
                fac.save(update_fields=["tenant_id", "updated_at"])
            facilities.append(fac)
        self._summary["facilities"] = len(facilities)

        # Minimal structural depth for the main hospital: one building, wards
        # for cardiac / ICU / NICU / general, 21 ORs, and beds up to ~265.
        main = facilities[0]
        building, _ = Building.objects.get_or_create(
            facility=main,
            code="MAIN-BLDG",
            defaults={"tenant_id": tenant_id, "name": "Main Hospital Building"},
        )
        # We create ONE department per structural area we care about; wards
        # under those departments; then a handful of representative rooms
        # (OR, NICU, cardiac ICU, general). Bed counts are approximate: full
        # 265-bed inventory would bloat the seed for no demo value.
        dept_specs = [
            ("CARD", "Cardiology & Cardiac Surgery"),
            ("ICU", "Adult Intensive Care"),
            ("NICU", "Neonatal Intensive Care"),
            ("OR", "Operating Theatres"),
            ("WARD", "General Inpatient Wards"),
        ]
        depts = {}
        for code, name in dept_specs:
            dept, _ = Department.objects.get_or_create(
                facility=main,
                code=code,
                defaults={"tenant_id": tenant_id, "name": name},
            )
            depts[code] = dept

        ward_specs = [
            ("CARD", "CARD-W1", "Cardiac Step-Down Ward"),
            ("ICU", "ICU-W1", "Adult ICU"),
            ("NICU", "NICU-W1", "NICU"),
            ("OR", "OR-W1", "Operating Rooms"),
            ("WARD", "GEN-W1", "General Ward — West"),
            ("WARD", "GEN-W2", "General Ward — East"),
        ]
        wards = {}
        for dcode, wcode, wname in ward_specs:
            ward, _ = Ward.objects.get_or_create(
                department=depts[dcode],
                code=wcode,
                defaults={"tenant_id": tenant_id, "name": wname},
            )
            wards[wcode] = ward

        # 21 operating rooms
        for i in range(1, 22):
            room, _ = Room.objects.get_or_create(
                ward=wards["OR-W1"],
                room_number=f"OR-{i:02d}",
                defaults={"tenant_id": tenant_id, "room_type": "operating"},
            )
            Bed.objects.get_or_create(
                room=room,
                bed_number=f"OR-{i:02d}-01",
                defaults={"tenant_id": tenant_id, "status": "available"},
            )

        # 28 NICU incubators
        for i in range(1, 29):
            room, _ = Room.objects.get_or_create(
                ward=wards["NICU-W1"],
                room_number=f"NICU-{i:02d}",
                defaults={"tenant_id": tenant_id, "room_type": "icu"},
            )
            Bed.objects.get_or_create(
                room=room,
                bed_number=f"INC-{i:02d}",
                defaults={"tenant_id": tenant_id, "status": "available"},
            )

        # ~40 adult ICU + cardiac step-down beds
        for i in range(1, 21):
            room, _ = Room.objects.get_or_create(
                ward=wards["ICU-W1"],
                room_number=f"ICU-{i:02d}",
                defaults={"tenant_id": tenant_id, "room_type": "icu"},
            )
            Bed.objects.get_or_create(
                room=room,
                bed_number=f"ICU-{i:02d}-01",
                defaults={"tenant_id": tenant_id, "status": "available"},
            )
        for i in range(1, 21):
            room, _ = Room.objects.get_or_create(
                ward=wards["CARD-W1"],
                room_number=f"CARD-{i:02d}",
                defaults={"tenant_id": tenant_id, "room_type": "standard"},
            )
            Bed.objects.get_or_create(
                room=room,
                bed_number=f"CARD-{i:02d}-01",
                defaults={"tenant_id": tenant_id, "status": "available"},
            )

    # ------------------------------------------------------------------
    # C) Practitioners
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_practitioners(self, tenant_id: uuid.UUID) -> None:
        from products.cymed.core.providers.models import (
            Provider,
            ProviderCredential,
            ProviderLicense,
            ProviderSpecialty,
            ProviderType,
        )

        firsts_m = self._ref["first_m"]
        firsts_f = self._ref["first_f"]
        lasts = self._ref["last"]
        specialties = self._ref["specialties"]

        count = 60
        self._provider_ids: list[uuid.UUID] = []
        for i in range(count):
            male = random.random() < 0.55
            first = random.choice(firsts_m if male else firsts_f)
            last = random.choice(lasts)
            npi = f"JO-NPI-{i:06d}"
            prov, _ = Provider.objects.update_or_create(
                npi=npi,
                defaults={
                    "tenant_id": tenant_id,
                    "user_id": uuid.uuid4(),
                    "first_name": first,
                    "last_name": last,
                    "provider_type": ProviderType.PHYSICIAN,
                    "is_active": True,
                },
            )
            if prov.tenant_id != tenant_id:
                prov.tenant_id = tenant_id
                prov.save(update_fields=["tenant_id", "updated_at"])
            self._provider_ids.append(prov.id)

            spec = specialties[i % len(specialties)]
            ProviderSpecialty.objects.get_or_create(
                provider=prov,
                specialty_code=spec.upper().replace(" ", "_")[:80],
                defaults={"tenant_id": tenant_id, "specialty_display": spec},
            )
            ProviderCredential.objects.get_or_create(
                provider=prov,
                title="MD",
                issuer="Jordan Medical Council",
                defaults={"tenant_id": tenant_id, "date_issued": date(2005, 1, 1)},
            )
            ProviderLicense.objects.get_or_create(
                provider=prov,
                license_number=f"JMC-{i:05d}",
                defaults={
                    "tenant_id": tenant_id,
                    "state_issued": "Jordan",
                    "expiry_date": date(timezone.now().year + 3, 12, 31),
                },
            )
        self._summary["practitioners"] = count

    # ------------------------------------------------------------------
    # D) Insurers
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_insurers(
        self, tenant_id: uuid.UUID, profile_ids: list[uuid.UUID]
    ) -> None:
        from products.cymed.payments.models import InsurancePolicy

        if not profile_ids:
            return

        # InsurancePolicy requires an owning PatientPortalProfile — the
        # model has no free-standing "insurer registry" table. We attach
        # one template policy per payer to the first available profile so
        # every payer surfaces in the tenant. This is a demo convention, not
        # a real member policy.
        anchor_profile_id = profile_ids[0]
        for payer in self._ref["insurers"]:
            InsurancePolicy.objects.update_or_create(
                profile_id=anchor_profile_id,
                insurer_code=payer["code"],
                policy_number="TEMPLATE-DEMO",
                defaults={
                    "tenant_id": tenant_id,
                    "member_no": "TEMPLATE",
                    "network_tier": "other",
                    "co_pay_percent": Decimal("20.00"),
                    "valid_from": date(2025, 1, 1),
                    "valid_to": date(2027, 12, 31),
                    "pre_auth_required": [],
                    "excluded_services": [],
                    "verified_at": timezone.now(),
                    "verified_via": "manual",
                },
            )

    # ------------------------------------------------------------------
    # E) Catalog — imaging, lab, DTC, pharmacy
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_catalog(self, tenant_id: uuid.UUID) -> None:
        from products.cymed.imaging.patient_booking.models import BookableStudy
        from products.cymed.laboratory.dtc_catalog.models import (
            DtcCategory,
            DtcProduct,
        )
        from products.cymed.laboratory.online_booking.models import (
            BookableTest,
            LabPackage,
        )
        from products.cymed.pharmacy.ecommerce.models import PharmacyProduct

        # 40 bookable imaging studies
        for i, (modality, body) in enumerate(_IMAGING_CATALOG[:40]):
            base_price = {
                "xray": Decimal("35"),
                "ct": Decimal("180"),
                "mri": Decimal("320"),
                "us": Decimal("60"),
                "mammo": Decimal("90"),
                "dexa": Decimal("110"),
                "nucmed": Decimal("250"),
                "pet": Decimal("650"),
                "fluoro": Decimal("200"),
                "dental": Decimal("45"),
            }.get(modality, Decimal("120"))
            code = f"IMG-{modality.upper()}-{i:03d}"
            BookableStudy.objects.update_or_create(
                tenant_id=tenant_id,
                code=code,
                defaults={
                    "name": f"{modality.upper()} — {body}",
                    "name_ar": f"{modality.upper()} — {body}",
                    "modality": modality,
                    "body_part": body,
                    "contrast_required": modality in ("ct", "mri") and (i % 3 == 0),
                    "duration_minutes": 15 if modality in ("xray", "us") else 30,
                    "price": base_price,
                    "currency": "JOD",
                    "vat_rate": Decimal("0.16"),
                    "requires_referral": modality in ("mri", "ct", "pet", "nucmed"),
                    "active": True,
                },
            )

        # 60 bookable lab tests
        for i, (category, code_suffix, name) in enumerate(_LAB_CATALOG[:60]):
            price_by_cat = {
                "hematology": Decimal("18"),
                "chemistry": Decimal("22"),
                "endocrine": Decimal("32"),
                "vitamins": Decimal("40"),
                "cardiac": Decimal("55"),
                "tumor_markers": Decimal("60"),
                "serology": Decimal("35"),
                "reproductive": Decimal("28"),
                "urine": Decimal("14"),
                "stool": Decimal("16"),
                "micro": Decimal("42"),
            }.get(category, Decimal("25"))
            BookableTest.objects.update_or_create(
                tenant_id=tenant_id,
                code=f"LAB-{code_suffix}",
                defaults={
                    "name": name,
                    "name_ar": name,
                    "category": category,
                    "specimen_type": (
                        "urine"
                        if category == "urine"
                        else ("stool" if category == "stool" else "blood")
                    ),
                    "turnaround_hours": 24,
                    "fasting_required": code_suffix
                    in ("GLUC_FBS", "LIPID", "INSULIN"),
                    "price": price_by_cat,
                    "currency": "JOD",
                    "vat_rate": Decimal("0.16"),
                    "requires_prescription": category in ("cardiac", "tumor_markers"),
                    "active": True,
                },
            )

        # 15 lab packages
        for code, name in _LAB_PACKAGES:
            LabPackage.objects.update_or_create(
                tenant_id=tenant_id,
                code=code,
                defaults={
                    "name": name,
                    "name_ar": name,
                    "description": f"Pre-composed package: {name}",
                    "price": Decimal("120.00"),
                    "currency": "JOD",
                    "vat_rate": Decimal("0.16"),
                    "discount_percent": Decimal("10.00"),
                    "active": True,
                },
            )

        # 20 DTC wellness kits
        dtc_cat, _ = DtcCategory.objects.update_or_create(
            tenant_id=tenant_id,
            code="WELLNESS",
            defaults={
                "name": "Wellness Kits",
                "name_ar": "أطقم الصحة",
                "display_order": 1,
                "active": True,
            },
        )
        for code, name in _DTC_PRODUCTS:
            DtcProduct.objects.update_or_create(
                tenant_id=tenant_id,
                code=code,
                defaults={
                    "category": dtc_cat,
                    "name": name,
                    "name_ar": name,
                    "tagline": "Home-collect wellness insight",
                    "description": f"Direct-to-consumer kit: {name}",
                    "kind": DtcProduct.Kind.WELLNESS_PANEL,
                    "tests_included": [],
                    "specimen_type": DtcProduct.SpecimenType.BLOOD,
                    "collection_mode": DtcProduct.CollectionMode.HOME_KIT,
                    "turnaround_days": 5,
                    "includes_consultation": True,
                    "price": Decimal("95.00"),
                    "currency": "JOD",
                    "vat_rate": Decimal("0.16"),
                    "stock_qty": -1,
                    "active": True,
                },
            )

        # 60 OTC + 40 Rx pharmacy products
        otc_pool = self._ref["otc"]
        rx_pool = self._ref["rx"]
        for i in range(60):
            src = otc_pool[i % len(otc_pool)]
            PharmacyProduct.objects.update_or_create(
                tenant_id=tenant_id,
                sku=f"OTC-{i:04d}",
                defaults={
                    "name": src.get("name", f"OTC-{i}"),
                    "name_ar": src.get("name", f"OTC-{i}"),
                    "kind": PharmacyProduct.Kind.OTC,
                    "requires_prescription": False,
                    "price": src.get("price", Decimal("3.00")),
                    "currency": "JOD",
                    "vat_rate": Decimal("0.16"),
                    "stock_qty": 500,
                    "active": True,
                },
            )
        for i in range(40):
            src = rx_pool[i % len(rx_pool)]
            PharmacyProduct.objects.update_or_create(
                tenant_id=tenant_id,
                sku=f"RX-{i:04d}",
                defaults={
                    "name": src.get("name", f"RX-{i}"),
                    "name_ar": src.get("name", f"RX-{i}"),
                    "kind": PharmacyProduct.Kind.RX,
                    "requires_prescription": True,
                    "price": src.get("price", Decimal("8.00")),
                    "currency": "JOD",
                    "vat_rate": Decimal("0.16"),
                    "stock_qty": 200,
                    "active": True,
                },
            )

    # ------------------------------------------------------------------
    # F) Patients
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_patients(
        self, tenant_id: uuid.UUID, count: int
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        import uuid as _uuid

        from products.cymed.core.patients.models import (
            GenderType,
            Patient,
            PatientAddress,
            PatientContact,
        )
        from products.cymed.patient_portal.models import NFCCard, PatientPortalProfile

        firsts_m = self._ref["first_m"]
        firsts_f = self._ref["first_f"]
        lasts = self._ref["last"]
        cities = self._ref["cities"]

        today = date.today()
        patient_ids: list[uuid.UUID] = []
        profile_ids: list[uuid.UUID] = []
        first_mrns: list[str] = []

        for i in range(count):
            is_female = random.random() < 0.52
            first = random.choice(firsts_f if is_female else firsts_m)
            last = random.choice(lasts)
            age_days = random.randint(0, 365 * 90)
            dob = today - timedelta(days=age_days)
            mrn = f"SHA-{i + 1:06d}"
            national_id = "".join(str(random.randint(0, 9)) for _ in range(10))
            mobile_last = "".join(str(random.randint(0, 9)) for _ in range(8))
            mobile = f"+9627{mobile_last}"
            city = random.choice(cities)
            gender = GenderType.FEMALE if is_female else GenderType.MALE

            patient, _ = Patient.objects.update_or_create(
                mrn=mrn,
                defaults={
                    "tenant_id": tenant_id,
                    "first_name": first,
                    "last_name": last,
                    "dob": dob,
                    "gender": gender,
                    "national_id": national_id,
                    "is_active": True,
                },
            )
            if patient.tenant_id != tenant_id:
                patient.tenant_id = tenant_id
                patient.save(update_fields=["tenant_id", "updated_at"])
            patient_ids.append(patient.id)
            if len(first_mrns) < 3:
                first_mrns.append(mrn)

            PatientContact.objects.get_or_create(
                patient=patient,
                telecom_system="phone",
                telecom_value=mobile,
                defaults={"tenant_id": tenant_id, "use": "mobile"},
            )
            PatientAddress.objects.get_or_create(
                patient=patient,
                line1=f"{random.randint(1, 200)} Al-Salam Street",
                defaults={
                    "tenant_id": tenant_id,
                    "city": city,
                    "country": "Jordan",
                    "use": "home",
                },
            )

            # Portal profile for every patient — needed as an FK anchor for
            # bills, bookings, orders, and rewards. The spec's "5% get
            # PatientPortalProfile" originally described only opted-in app
            # users; keeping profiles universal but marking most as
            # non-activated preserves the intent without breaking bill FKs.
            profile, _ = PatientPortalProfile.objects.update_or_create(
                patient=patient,
                defaults={
                    "tenant_id": tenant_id,
                    "email_verified": False,
                    "phone_verified": True,
                    "two_factor_enabled": False,
                    "preferred_language": "ar",
                    "theme_preference": "system",
                    "emergency_access_enabled": True,
                    "data_sharing_consent": False,
                },
            )
            profile_ids.append(profile.id)

            if random.random() < 0.05:
                NFCCard.objects.get_or_create(
                    profile=profile,
                    card_uuid=_uuid.uuid4(),
                    defaults={
                        "tenant_id": tenant_id,
                        "public_key_pem": "-----BEGIN PUBLIC KEY-----\nDEMO\n-----END PUBLIC KEY-----",
                        "chip_vendor": "desfire_ev3",
                        "activated_at": timezone.now(),
                    },
                )
                profile.nfc_card_activated = True
                profile.save(update_fields=["nfc_card_activated", "updated_at"])

        self._summary["patients"] = count
        self._summary["first_mrns"] = first_mrns
        return patient_ids, profile_ids

    # ------------------------------------------------------------------
    # G) Encounters (+ orders, prescriptions, CDS alerts)
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_encounters(
        self,
        tenant_id: uuid.UUID,
        org_id: uuid.UUID,
        patient_ids: list[uuid.UUID],
        count: int,
    ) -> list[uuid.UUID]:
        from products.cymed.ai_cds.models import CDSAlert
        from products.cymed.core.encounters.models import (
            Encounter,
            EncounterDiagnosis,
            EncounterParticipant,
            EncounterReason,
            EncounterStatus,
            EncounterType,
        )
        from products.cymed.core.facilities.models import Facility
        from products.cymed.core.orders.models import (
            Order,
            OrderItem,
            OrderType,
        )
        from products.cymed.pharmacy.prescriptions.models import (
            Prescription,
            PrescriptionItem,
            PrescriptionStatus,
            PrescriptionType,
        )

        main_facility = Facility.objects.filter(
            tenant_id=tenant_id, code="SHA-MAIN"
        ).first()
        if main_facility is None:
            main_facility = Facility.objects.filter(tenant_id=tenant_id).first()
        opc_facility = (
            Facility.objects.filter(tenant_id=tenant_id, code="SHA-OPC").first()
            or main_facility
        )

        complaints = self._ref["complaints"]
        rx_pool = self._ref["rx"]
        encounter_types = [
            EncounterType.OUTPATIENT,
            EncounterType.OUTPATIENT,
            EncounterType.OUTPATIENT,
            EncounterType.EMERGENCY,
            EncounterType.INPATIENT,
            EncounterType.TELEMEDICINE,
        ]

        now = timezone.now()
        encounter_ids: list[uuid.UUID] = []
        for i in range(count):
            patient_id = random.choice(patient_ids)
            provider_id = random.choice(self._provider_ids)
            etype = random.choice(encounter_types)
            facility = (
                main_facility
                if etype in (EncounterType.INPATIENT, EncounterType.EMERGENCY)
                else opc_facility
            )
            offset_minutes = random.randint(0, 60 * 24 * 60)
            start = now - timedelta(minutes=offset_minutes)
            duration = timedelta(minutes=random.randint(20, 240))
            end = start + duration
            end_final = end if random.random() < 0.9 else None
            status = (
                EncounterStatus.FINISHED
                if end_final is not None
                else EncounterStatus.IN_PROGRESS
            )
            enc = Encounter.objects.create(
                tenant_id=tenant_id,
                patient_id=patient_id,
                encounter_type=etype,
                status=status,
                start_time=start,
                end_time=end_final,
                organization_id=org_id,
                facility=facility,
            )
            encounter_ids.append(enc.id)

            EncounterParticipant.objects.create(
                tenant_id=tenant_id,
                encounter=enc,
                provider_id=provider_id,
                role="attending",
            )
            reason = random.choice(complaints)
            EncounterReason.objects.create(
                tenant_id=tenant_id,
                encounter=enc,
                reason_code="R00-R99",
                reason_text=reason,
            )
            EncounterDiagnosis.objects.create(
                tenant_id=tenant_id,
                encounter=enc,
                condition_code="MG30.0",
                display=reason.split("/")[-1].strip(),
                use="chief_complaint",
            )

            # 0..3 lab orders
            for j in range(random.randint(0, 3)):
                order = Order.objects.create(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    encounter=enc,
                    order_type=OrderType.LABORATORY,
                    priority="routine",
                    status="active",
                    ordered_by=str(provider_id),
                    ordered_at=start,
                )
                OrderItem.objects.create(
                    tenant_id=tenant_id,
                    order=order,
                    code=f"LAB-{j:02d}",
                    display=random.choice(
                        ["CBC", "CMP", "HbA1c", "Lipid Panel", "TSH"]
                    ),
                    quantity=1,
                )

            # 0..2 imaging orders
            for j in range(random.randint(0, 2)):
                order = Order.objects.create(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    encounter=enc,
                    order_type=OrderType.IMAGING,
                    priority="routine",
                    status="active",
                    ordered_by=str(provider_id),
                    ordered_at=start,
                )
                OrderItem.objects.create(
                    tenant_id=tenant_id,
                    order=order,
                    code=f"IMG-{j:02d}",
                    display=random.choice(
                        ["Chest X-Ray", "CT Brain", "US Abdomen", "MRI Knee"]
                    ),
                    quantity=1,
                )

            # 0..2 prescriptions
            for j in range(random.randint(0, 2)):
                src = random.choice(rx_pool)
                rx = Prescription.objects.create(
                    tenant_id=tenant_id,
                    prescription_number=f"RX-{i:06d}-{j:02d}-{uuid.uuid4().hex[:6].upper()}",
                    patient_id=patient_id,
                    encounter_id=enc.id,
                    prescriber_id=provider_id,
                    prescription_type=PrescriptionType.OUTPATIENT,
                    status=PrescriptionStatus.ACTIVE,
                    diagnosis_codes=["MG30.0"],
                    clinical_notes=reason,
                    valid_from=start.date(),
                    valid_until=(start + timedelta(days=30)).date(),
                    refills_authorized=1,
                )
                PrescriptionItem.objects.create(
                    tenant_id=tenant_id,
                    prescription=rx,
                    drug_code=f"RXNORM-{j:05d}",
                    drug_name=src.get("name", "Amoxicillin 500mg"),
                    dose="500",
                    dose_unit="mg",
                    route="Oral",
                    frequency="BID",
                    duration="7 days",
                    quantity=Decimal("14"),
                    quantity_unit="tablet",
                    days_supply=7,
                    sig=f"Take as directed for: {reason}",
                )

            # 20% CDSS alerts
            if random.random() < 0.20:
                CDSAlert.objects.create(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    encounter_id=enc.id,
                    kind=random.choice(
                        [
                            "drug_interaction",
                            "drug_allergy",
                            "dose_warning",
                            "sepsis_early_warning",
                            "fall_risk",
                        ]
                    ),
                    severity=random.choice(["low", "medium", "high"]),
                    title="CDS advisory (demo)",
                    detail=f"Demo CDS advisory generated for encounter {enc.id}.",
                    context={"reason": reason},
                    score=Decimal("0.720"),
                )

        self._summary["encounters"] = count
        return encounter_ids

    # ------------------------------------------------------------------
    # H, I, J, K) Ecosystem + home collection + DTC + loyalty
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_referrals_and_extras(
        self, tenant_id: uuid.UUID, profile_ids: list[uuid.UUID]
    ) -> None:
        from products.cymed.ecosystem.referral_routing.models import NetworkReferral
        from products.cymed.ecosystem.rewards.models import (
            EcosystemAccount,
            EcosystemProgram,
        )
        from products.cymed.laboratory.dtc_catalog.models import (
            DtcOrder,
            DtcProduct,
        )
        from products.cymed.laboratory.home_collection.models import (
            HomeCollectionBooking,
            HomeCollectionSlot,
            Phlebotomist,
        )

        if not profile_ids:
            return

        # H) 15 cross-provider referrals
        target_kinds = [
            NetworkReferral.TargetKind.LAB,
            NetworkReferral.TargetKind.IMAGING,
            NetworkReferral.TargetKind.PHARMACY,
            NetworkReferral.TargetKind.HOSPITAL,
            NetworkReferral.TargetKind.CLINIC,
        ]
        for i in range(15):
            NetworkReferral.objects.create(
                tenant_id=tenant_id,
                source_tenant_id=tenant_id,
                target_tenant_id=uuid.uuid4(),
                target_kind=random.choice(target_kinds),
                patient_profile_id=random.choice(profile_ids),
                reason=random.choice(self._ref["complaints"]),
                clinical_summary="Cross-provider demo referral.",
                urgency=random.choice(
                    [
                        NetworkReferral.Urgency.ROUTINE,
                        NetworkReferral.Urgency.URGENT,
                    ]
                ),
                status=NetworkReferral.Status.ROUTED,
                routed_at=timezone.now(),
            )

        # I) 20 home-collection bookings — requires a phlebotomist + slot
        phleb, _ = Phlebotomist.objects.get_or_create(
            tenant_id=tenant_id,
            license_number="JMC-PHLEB-0001",
            defaults={
                "user_profile_id": uuid.uuid4(),
                "first_name": "Layla",
                "last_name": "Al-Zoubi",
                "phone": "+962791234567",
                "vehicle_plate": "JO 12345",
                "active": True,
                "coverage_cities": ["Amman", "Zarqa"],
                "cold_chain_capable": True,
            },
        )
        today = date.today()
        slot, _ = HomeCollectionSlot.objects.get_or_create(
            tenant_id=tenant_id,
            phlebotomist=phleb,
            date=today,
            start_time=time(7, 0),
            end_time=time(11, 0),
            defaults={"capacity": 40, "booked_count": 0, "status": "open"},
        )
        for i in range(20):
            HomeCollectionBooking.objects.create(
                tenant_id=tenant_id,
                patient_profile_id=random.choice(profile_ids),
                slot=slot,
                phlebotomist=phleb,
                address={"line1": f"{i + 1} Wasfi Al-Tal St", "city": "Amman"},
                tests_requested=[{"code": "LAB-CBC", "name": "CBC"}],
                fasting_required=random.random() < 0.5,
                status=random.choice(
                    [
                        HomeCollectionBooking.Status.CONFIRMED,
                        HomeCollectionBooking.Status.COLLECTED,
                        HomeCollectionBooking.Status.DELIVERED_TO_LAB,
                    ]
                ),
                payment_status=HomeCollectionBooking.PaymentStatus.PAID,
            )

        # J) 15 DTC orders
        dtc_products = list(DtcProduct.objects.filter(tenant_id=tenant_id)[:20])
        if dtc_products:
            for i in range(15):
                DtcOrder.objects.create(
                    tenant_id=tenant_id,
                    patient_profile_id=random.choice(profile_ids),
                    product=random.choice(dtc_products),
                    shipping_address={
                        "line1": f"{i + 1} Rainbow St",
                        "city": "Amman",
                    },
                    status=random.choice(
                        [
                            DtcOrder.Status.PLACED,
                            DtcOrder.Status.KIT_DISPATCHED,
                            DtcOrder.Status.SAMPLE_RECEIVED,
                            DtcOrder.Status.RESULTS_READY,
                        ]
                    ),
                )

        # K) Loyalty — 40% enrolment
        program, _ = EcosystemProgram.objects.update_or_create(
            code="SHA_LOYALTY",
            defaults={
                "tenant_id": tenant_id,
                "name": "Specialized Care Rewards",
                "name_ar": "مكافآت الرعاية المتخصصة",
                "currency_conversion": Decimal("1.0"),
                "redeem_ratio": Decimal("100"),
                "cross_country_convertible": False,
                "active": True,
            },
        )
        enrolled_count = int(len(profile_ids) * 0.4)
        for pid in random.sample(profile_ids, k=min(enrolled_count, len(profile_ids))):
            EcosystemAccount.objects.get_or_create(
                program=program,
                patient_profile_id=pid,
                defaults={
                    "tenant_id": tenant_id,
                    "primary_country": "JO",
                    "balance_points": random.randint(0, 5000),
                    "lifetime_points": random.randint(0, 20000),
                    "current_tier": random.choice(["silver", "gold", "platinum"]),
                },
            )

    # ------------------------------------------------------------------
    # L, M) Bills + claims
    # ------------------------------------------------------------------

    @transaction.atomic
    def _seed_bills_and_claims(
        self,
        tenant_id: uuid.UUID,
        encounter_ids: list[uuid.UUID],
        profile_ids: list[uuid.UUID],
    ) -> None:
        from products.cymed.core.encounters.models import Encounter
        from products.cymed.payments.models import (
            BillLineItem,
            UnifiedBill,
        )
        from products.cymed.rcm.models import AppealCase, Claim837

        if not encounter_ids or not profile_ids:
            return

        vat_rate = Decimal("0.16")
        outcomes = (
            ["paid"] * 60 + ["partial"] * 20 + ["patient_due"] * 10 + ["refunded"] * 10
        )
        random.shuffle(outcomes)

        total_billed = Decimal("0")
        total_paid = Decimal("0")
        sample_booking_ref = ""

        # Fetch encounter -> patient mapping in one query
        enc_map = {
            e.id: e.patient_id
            for e in Encounter.objects.filter(
                tenant_id=tenant_id, id__in=encounter_ids
            ).only("id", "patient_id")
        }
        # Map patient_id -> profile_id
        from products.cymed.patient_portal.models import PatientPortalProfile

        prof_map = {
            p.patient_id: p.id
            for p in PatientPortalProfile.objects.filter(
                tenant_id=tenant_id, patient_id__in=list(enc_map.values())
            ).only("id", "patient_id")
        }

        for idx, enc_id in enumerate(encounter_ids):
            patient_id = enc_map.get(enc_id)
            if patient_id is None:
                continue
            profile_id = prof_map.get(patient_id)
            if profile_id is None:
                continue

            status = outcomes[idx % len(outcomes)]
            bill = UnifiedBill.objects.create(
                tenant_id=tenant_id,
                patient_profile_id=profile_id,
                encounter_ids=[str(enc_id)],
                status="draft",
                issued_at=timezone.now(),
            )
            line_count = random.randint(1, 5)
            for j in range(line_count):
                category = random.choice(
                    ["consultation", "procedure", "medication", "lab", "imaging"]
                )
                unit_price = Decimal(str(random.randint(15, 800)))
                qty = Decimal("1")
                amount = unit_price * qty
                line_vat = (amount * vat_rate).quantize(Decimal("0.01"))
                BillLineItem.objects.create(
                    tenant_id=tenant_id,
                    bill=bill,
                    provider_tenant_id=tenant_id,
                    encounter_id=enc_id,
                    service_code=f"SRV-{category.upper()}-{j:03d}",
                    service_name=f"{category.title()} service #{j + 1}",
                    quantity=qty,
                    unit_price=unit_price,
                    amount=amount,
                    vat=line_vat,
                    category=category,
                    insurance_paid=Decimal("0"),
                )
            bill.recompute()
            bill.refresh_from_db()

            total_billed += bill.total
            if status == "paid":
                bill.status = "paid"
                bill.paid_at = timezone.now()
                bill.jofotara_uuid = f"JO-DEMO-{uuid.uuid4().hex[:8].upper()}"
                bill.jofotara_qr = "DEMO-QR"
                bill.insurance_paid = Decimal("0")
                bill.patient_due = Decimal("0")
                bill.save(
                    update_fields=[
                        "status",
                        "paid_at",
                        "jofotara_uuid",
                        "jofotara_qr",
                        "insurance_paid",
                        "patient_due",
                        "updated_at",
                    ]
                )
                total_paid += bill.total
                if not sample_booking_ref:
                    sample_booking_ref = bill.bill_number
            elif status == "partial":
                pay = (bill.total / Decimal("2")).quantize(Decimal("0.01"))
                bill.status = "partial"
                bill.insurance_paid = pay
                bill.patient_due = bill.total - pay
                bill.save(
                    update_fields=[
                        "status",
                        "insurance_paid",
                        "patient_due",
                        "updated_at",
                    ]
                )
                total_paid += pay
            elif status == "patient_due":
                bill.status = "patient_due"
                bill.save(update_fields=["status", "updated_at"])
            elif status == "refunded":
                bill.status = "cancelled"
                bill.save(update_fields=["status", "updated_at"])

        self._summary["total_billed"] = total_billed
        self._summary["total_paid"] = total_paid
        self._summary["sample_booking_ref"] = sample_booking_ref

        # M) 40 claims + 8 appeals
        bills = list(
            UnifiedBill.objects.filter(tenant_id=tenant_id).order_by("-created_at")[:40]
        )
        payer_codes = [p["code"] for p in self._ref["insurers"]]
        claims: list = []
        for i, bill in enumerate(bills):
            enc_id_str = (bill.encounter_ids or [None])[0]
            try:
                enc_uuid = uuid.UUID(enc_id_str) if enc_id_str else uuid.uuid4()
            except (TypeError, ValueError):
                enc_uuid = uuid.uuid4()
            scrub_errors: list = []
            if i % 5 == 0:
                scrub_errors = [
                    {
                        "code": "MISSING_MODIFIER",
                        "detail": "Procedure missing laterality modifier.",
                    }
                ]
            claim = Claim837.objects.create(
                tenant_id=tenant_id,
                bill_id=bill.id,
                encounter_id=enc_uuid,
                patient_profile_id=bill.patient_profile_id,
                kind="professional",
                payer_code=random.choice(payer_codes),
                payer_country="JO",
                diagnosis_codes=[{"icd11": "MG30.0", "primary": True}],
                procedure_codes=[{"cpt": "99213", "qty": 1}],
                charge_total=bill.total,
                status="scrubbed" if scrub_errors else "submitted",
                scrub_errors=scrub_errors,
                submitted_at=timezone.now(),
            )
            claims.append(claim)

        for claim in claims[:8]:
            AppealCase.objects.create(
                tenant_id=tenant_id,
                claim=claim,
                level=1,
                status="submitted",
                denial_codes_addressed=[{"carc": "197", "rarc": "N30"}],
                appeal_letter_html="<p>Demo appeal letter.</p>",
                submitted_at=timezone.now(),
                recovered_amount=Decimal("0"),
            )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _print_summary(self, tenant_id: uuid.UUID) -> None:
        s = self._summary
        lines = [
            "=============================",
            " Specialized Hospital Amman",
            " Demo tenant seeded OK",
            "=============================",
            f" Tenant:            {tenant_id}",
            f" Facilities:        {s['facilities']}",
            f" Practitioners:     {s['practitioners']}",
            f" Patients:          {s['patients']}",
            f" Encounters:        {s['encounters']}",
            f" Total billed:      {s['total_billed']} JOD",
            f" Total paid:        {s['total_paid']} JOD",
            f" First 3 MRNs:      {', '.join(s['first_mrns'])}",
            f" Sample booking ref:{s['sample_booking_ref']}",
            "=============================",
        ]
        self.stdout.write("\n".join(lines))
