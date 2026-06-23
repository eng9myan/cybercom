"""
Data migration: seeds the CyMed product catalog and editions.
Products: Clinic, Hospital, Laboratory, Imaging, Pharmacy,
          Patient Portal, Provider Portal, Population Health.
"""
from django.db import migrations
import uuid


PRODUCTS = [
    {"code": "cymed_clinic",           "name": "CyMed Clinic",            "version": "1.0.0"},
    {"code": "cymed_hospital",         "name": "CyMed Hospital",           "version": "1.0.0"},
    {"code": "cymed_laboratory",       "name": "CyMed Laboratory",         "version": "1.0.0"},
    {"code": "cymed_imaging",          "name": "CyMed Imaging",            "version": "1.0.0"},
    {"code": "cymed_pharmacy",         "name": "CyMed Pharmacy",           "version": "1.0.0"},
    {"code": "cymed_patient_portal",   "name": "CyMed Patient Portal",     "version": "1.0.0"},
    {"code": "cymed_provider_portal",  "name": "CyMed Provider Portal",    "version": "1.0.0"},
    {"code": "cymed_population_health","name": "CyMed Population Health",  "version": "1.0.0"},
]

EDITIONS = [
    # Clinic
    {"product": "cymed_clinic", "code": "starter",      "name": "CyMed Clinic Starter",      "tier": "starter",            "max_users": 10,  "max_providers": 5,   "max_beds": 0,   "max_facilities": 1,  "max_clinics": 1,  "sort_order": 1},
    {"product": "cymed_clinic", "code": "professional", "name": "CyMed Clinic Professional",  "tier": "professional",       "max_users": 50,  "max_providers": 20,  "max_beds": 0,   "max_facilities": 3,  "max_clinics": 3,  "sort_order": 2},
    {"product": "cymed_clinic", "code": "enterprise",   "name": "CyMed Clinic Enterprise",    "tier": "enterprise",         "max_users": 0,   "max_providers": 0,   "max_beds": 0,   "max_facilities": 0,  "max_clinics": 0,  "sort_order": 3},
    # Hospital
    {"product": "cymed_hospital", "code": "community",  "name": "CyMed Community Hospital",   "tier": "community",          "max_users": 200, "max_providers": 50,  "max_beds": 100, "max_facilities": 1,  "max_clinics": 0,  "sort_order": 1},
    {"product": "cymed_hospital", "code": "enterprise", "name": "CyMed Enterprise Hospital",  "tier": "enterprise_hospital","max_users": 0,   "max_providers": 0,   "max_beds": 500, "max_facilities": 5,  "max_clinics": 0,  "sort_order": 2},
    {"product": "cymed_hospital", "code": "medical_city","name": "CyMed Medical City",        "tier": "medical_city",       "max_users": 0,   "max_providers": 0,   "max_beds": 0,   "max_facilities": 0,  "max_clinics": 0,  "sort_order": 3},
    # Laboratory
    {"product": "cymed_laboratory", "code": "basic",       "name": "CyMed Laboratory Basic",    "tier": "basic",    "max_users": 20, "max_providers": 5,  "max_beds": 0, "max_facilities": 1, "max_clinics": 0, "sort_order": 1},
    {"product": "cymed_laboratory", "code": "advanced",    "name": "CyMed Laboratory Advanced", "tier": "advanced", "max_users": 0,  "max_providers": 0,  "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 2},
    {"product": "cymed_laboratory", "code": "reference",   "name": "CyMed Reference Lab",              "tier": "reference_lab",    "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 3},
    {"product": "cymed_laboratory", "code": "national",   "name": "CyMed National Laboratory Network", "tier": "national_network", "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 4},
    # Imaging
    {"product": "cymed_imaging", "code": "basic",       "name": "CyMed Imaging Basic",       "tier": "basic",      "max_users": 20, "max_providers": 5,  "max_beds": 0, "max_facilities": 1, "max_clinics": 0, "sort_order": 1},
    {"product": "cymed_imaging", "code": "enterprise",  "name": "CyMed Imaging Enterprise",  "tier": "enterprise", "max_users": 0,  "max_providers": 0,  "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 2},
    # Pharmacy
    {"product": "cymed_pharmacy", "code": "retail",            "name": "CyMed Pharmacy Retail",          "tier": "retail",            "max_users": 10,  "max_providers": 0,  "max_beds": 0, "max_facilities": 1,  "max_clinics": 0, "sort_order": 1},
    {"product": "cymed_pharmacy", "code": "chain",             "name": "CyMed Pharmacy Chain",           "tier": "chain",             "max_users": 0,   "max_providers": 0,  "max_beds": 0, "max_facilities": 0,  "max_clinics": 0, "sort_order": 2},
    {"product": "cymed_pharmacy", "code": "hospital_pharmacy", "name": "CyMed Hospital Pharmacy",        "tier": "hospital_pharmacy", "max_users": 0,   "max_providers": 0,  "max_beds": 0, "max_facilities": 0,  "max_clinics": 0, "sort_order": 3},
    # Portals
    {"product": "cymed_patient_portal",  "code": "standard",   "name": "CyMed Patient Portal Standard",   "tier": "starter",    "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 1},
    {"product": "cymed_patient_portal",  "code": "enterprise", "name": "CyMed Patient Portal Enterprise", "tier": "enterprise", "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 2},
    {"product": "cymed_patient_portal",  "code": "government", "name": "CyMed Patient Portal Government", "tier": "government", "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 3},
    {"product": "cymed_provider_portal", "code": "standard",   "name": "CyMed Provider Portal Standard",  "tier": "starter",    "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 1},
    {"product": "cymed_provider_portal", "code": "enterprise", "name": "CyMed Provider Portal Enterprise","tier": "enterprise", "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 2},
    # Population Health
    {"product": "cymed_population_health", "code": "standard",   "name": "CyMed Population Health Standard",   "tier": "starter",    "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 1},
    {"product": "cymed_population_health", "code": "enterprise", "name": "CyMed Population Health Enterprise", "tier": "enterprise", "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 2},
    {"product": "cymed_population_health", "code": "government", "name": "CyMed Population Health Government", "tier": "government", "max_users": 0, "max_providers": 0, "max_beds": 0, "max_facilities": 0, "max_clinics": 0, "sort_order": 3},
]

EDITION_MODULES = {
    "cymed_clinic:starter": [
        "clinic.appointments", "clinic.reception", "clinic.queues",
        "clinic.consultations", "clinic.telemedicine",
    ],
    "cymed_clinic:professional": [
        "clinic.appointments", "clinic.reception", "clinic.queues",
        "clinic.consultations", "clinic.telemedicine", "clinic.specialties",
        "clinic.referrals", "clinic.insurance_bridge",
    ],
    "cymed_clinic:enterprise": [
        "clinic.appointments", "clinic.reception", "clinic.queues",
        "clinic.consultations", "clinic.telemedicine", "clinic.specialties",
        "clinic.referrals", "clinic.insurance_bridge", "clinic.billing_bridge",
        "clinic.clinical_forms", "clinic.triage",
    ],
    "cymed_hospital:community": [
        "hospital.adt", "hospital.bed_management", "hospital.emergency",
        "hospital.inpatient", "hospital.nursing", "hospital.discharge",
    ],
    "cymed_hospital:enterprise": [
        "hospital.adt", "hospital.bed_management", "hospital.emergency",
        "hospital.inpatient", "hospital.nursing", "hospital.discharge",
        "hospital.icu", "hospital.operating_room", "hospital.anesthesia",
        "hospital.maternity", "hospital.transfer_center", "hospital.capacity_management",
    ],
    "cymed_hospital:medical_city": [
        "hospital.adt", "hospital.bed_management", "hospital.emergency",
        "hospital.inpatient", "hospital.nursing", "hospital.discharge",
        "hospital.icu", "hospital.operating_room", "hospital.anesthesia",
        "hospital.maternity", "hospital.transfer_center", "hospital.capacity_management",
        "hospital.clinical_command_center",
    ],
    "cymed_laboratory:basic": [
        "lab.orders", "lab.specimens", "lab.accessioning",
        "lab.worklists", "lab.results", "lab.blood_bank",
    ],
    "cymed_laboratory:advanced": [
        "lab.orders", "lab.specimens", "lab.accessioning",
        "lab.worklists", "lab.results", "lab.blood_bank",
        "lab.microbiology", "lab.pathology", "lab.histopathology",
        "lab.quality", "lab.analytics",
    ],
    "cymed_laboratory:reference": [
        "lab.orders", "lab.specimens", "lab.accessioning",
        "lab.worklists", "lab.results", "lab.blood_bank",
        "lab.microbiology", "lab.pathology", "lab.histopathology",
        "lab.quality", "lab.analytics",
        "lab.reference_lab", "lab.multi_site", "lab.cross_lab_routing",
    ],
    "cymed_laboratory:national": [
        "lab.orders", "lab.specimens", "lab.accessioning",
        "lab.worklists", "lab.results", "lab.blood_bank",
        "lab.microbiology", "lab.pathology", "lab.histopathology",
        "lab.quality", "lab.analytics",
        "lab.reference_lab", "lab.multi_site", "lab.cross_lab_routing",
        "lab.public_health", "lab.national_registry",
        "lab.population_analytics", "lab.government_integration",
    ],
}

# Sentinel tenant — commercial catalog is platform-level; use a fixed UUID
PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")


def seed_catalog(apps, schema_editor):
    ProductCatalogEntry = apps.get_model("commercial_editions", "ProductCatalogEntry")
    ProductEdition = apps.get_model("commercial_editions", "ProductEdition")
    EditionModule = apps.get_model("commercial_editions", "EditionModule")

    product_map = {}
    for p in PRODUCTS:
        obj, _ = ProductCatalogEntry.objects.get_or_create(
            code=p["code"],
            defaults={
                "id": uuid.uuid4(),
                "tenant_id": PLATFORM_TENANT,
                "name": p["name"],
                "current_version": p["version"],
                "is_active": True,
            },
        )
        product_map[p["code"]] = obj

    edition_map = {}
    for e in EDITIONS:
        product = product_map[e["product"]]
        obj, _ = ProductEdition.objects.get_or_create(
            product=product,
            code=e["code"],
            defaults={
                "id": uuid.uuid4(),
                "tenant_id": PLATFORM_TENANT,
                "name": e["name"],
                "tier": e["tier"],
                "is_active": True,
                "sort_order": e["sort_order"],
                "max_users": e["max_users"],
                "max_providers": e["max_providers"],
                "max_beds": e["max_beds"],
                "max_facilities": e["max_facilities"],
                "max_clinics": e["max_clinics"],
            },
        )
        edition_map[f"{e['product']}:{e['code']}"] = obj

    for key, modules in EDITION_MODULES.items():
        edition = edition_map.get(key)
        if not edition:
            continue
        for mod_code in modules:
            EditionModule.objects.get_or_create(
                edition=edition,
                module_code=mod_code,
                defaults={
                    "id": uuid.uuid4(),
                    "tenant_id": PLATFORM_TENANT,
                    "is_included": True,
                },
            )


def unseed_catalog(apps, schema_editor):
    ProductCatalogEntry = apps.get_model("commercial_editions", "ProductCatalogEntry")
    ProductCatalogEntry.objects.filter(
        code__in=[p["code"] for p in PRODUCTS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("commercial_editions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_catalog, unseed_catalog),
    ]
