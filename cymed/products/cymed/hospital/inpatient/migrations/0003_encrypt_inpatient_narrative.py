"""
Data migration: encrypt existing inpatient clinical free-text (plaintext from
before the fields became EncryptedText).

Per-tenant. Idempotent. Reverse no-op.
"""
from django.db import migrations

_TARGETS = {
    "DailyRound": ("subjective_notes", "objective_notes", "assessment_notes", "plan_notes"),
    "InpatientCarePlan": ("goals", "interventions"),
    "DischargePlanning": ("barriers_to_discharge",),
}


def encrypt_narrative(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.hospital.inpatient import models as m

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
        ("cymed_hospital_inpatient", "0002_alter_dailyround_assessment_notes_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_narrative, noop_reverse),
    ]
