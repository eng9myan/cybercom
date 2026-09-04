"""
Data migration: encrypt existing core clinical PHI text (plaintext from before
the fields became EncryptedText) — diagnosis / allergy / observation display
text, observation string values, clinical flags, risk factors.

Per-tenant. Idempotent. Reverse no-op.
"""
from django.db import migrations

_TARGETS = {
    "Condition": ("display",),
    "Allergy": ("substance_display",),
    "Observation": ("display", "value_string"),
    "ClinicalFlag": ("flag_text",),
    "RiskFactor": ("risk_display",),
}


def encrypt_phi(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.core.clinical import models as m

    for model_name, fields in _TARGETS.items():
        Model = getattr(m, model_name)
        tenant_ids = set(Model.objects.values_list("tenant_id", flat=True))
        for tid in tenant_ids:
            with tenant_context(tid):
                for row in Model.objects.filter(tenant_id=tid).iterator():
                    dirty = []
                    for name in fields:
                        val = getattr(row, name)
                        if val and val != "••••":
                            setattr(row, name, val)
                            dirty.append(name)
                    if dirty:
                        row.save(update_fields=[*dirty, "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cymed_clinical", "0002_alter_allergy_substance_display_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_phi, noop_reverse),
    ]
