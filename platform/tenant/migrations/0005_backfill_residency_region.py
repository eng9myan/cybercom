"""
M3: backfill Tenant.residency_region from home_region for rows created before
the field existed (canonical-data-model-v1.md §5.1 — residency_region is
required and immutable once set; home_region is the sensible seed).

Data-only, idempotent, reversible to a no-op.
"""
from django.db import migrations, models


def seed_residency_region(apps, schema_editor):
    Tenant = apps.get_model("platform_tenant", "Tenant")
    (
        Tenant.objects.filter(residency_region="")
        .exclude(home_region="")
        .update(residency_region=models.F("home_region"))
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("platform_tenant", "0004_tenant_compliance_flags_tenant_encryption_key_ref_and_more"),
    ]
    operations = [
        migrations.RunPython(seed_residency_region, noop_reverse),
    ]
