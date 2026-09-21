"""
Data migration: seeds EditionModule rows for cymed_pharmacy editions.

0002_seed_catalog created the cymed_pharmacy ProductEdition rows
(retail/chain/hospital_pharmacy) but never populated EDITION_MODULES for
them — clinic/hospital/laboratory/imaging all got module lists, pharmacy
did not. Standalone pharmacy tenants had no EditionModule rows to gate on.
"""

import uuid

from django.db import migrations

PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")

PHARMACY_EDITION_MODULES = {
    "retail": [
        "pharmacy.prescriptions",
        "pharmacy.dispensing",
        "pharmacy.formulary",
        "pharmacy.inventory",
    ],
    "chain": [
        "pharmacy.prescriptions",
        "pharmacy.dispensing",
        "pharmacy.formulary",
        "pharmacy.inventory",
        "pharmacy.procurement",
        "pharmacy.automation",
        "pharmacy.analytics",
    ],
    "hospital_pharmacy": [
        "pharmacy.prescriptions",
        "pharmacy.dispensing",
        "pharmacy.formulary",
        "pharmacy.inventory",
        "pharmacy.procurement",
        "pharmacy.automation",
        "pharmacy.analytics",
        "pharmacy.clinical",
        "pharmacy.interactions",
        "pharmacy.reconciliation",
        "pharmacy.hospital",
    ],
}


def seed_pharmacy_modules(apps, schema_editor):
    ProductCatalogEntry = apps.get_model("commercial_editions", "ProductCatalogEntry")
    ProductEdition = apps.get_model("commercial_editions", "ProductEdition")
    EditionModule = apps.get_model("commercial_editions", "EditionModule")

    try:
        product = ProductCatalogEntry.objects.get(code="cymed_pharmacy")
    except ProductCatalogEntry.DoesNotExist:
        return

    for edition_code, modules in PHARMACY_EDITION_MODULES.items():
        try:
            edition = ProductEdition.objects.get(product=product, code=edition_code)
        except ProductEdition.DoesNotExist:
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


def unseed_pharmacy_modules(apps, schema_editor):
    ProductCatalogEntry = apps.get_model("commercial_editions", "ProductCatalogEntry")
    EditionModule = apps.get_model("commercial_editions", "EditionModule")
    try:
        product = ProductCatalogEntry.objects.get(code="cymed_pharmacy")
    except ProductCatalogEntry.DoesNotExist:
        return
    EditionModule.objects.filter(edition__product=product).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("commercial_editions", "0003_editionfeature_attributes_editionfeature_created_by_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_pharmacy_modules, unseed_pharmacy_modules),
    ]
