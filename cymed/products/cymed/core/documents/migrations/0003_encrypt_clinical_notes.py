"""
Data migration: encrypt existing clinical free-text (plaintext from before the
fields became EncryptedText) across the documents app.

Per-tenant (encryption needs the tenant context). Idempotent — an already-
encrypted value is left alone. Reverse is a no-op.
"""
from django.db import migrations

# model label -> encrypted text field names
_TARGETS = {
    "ClinicalDocument": ("content",),
    "DocumentSection": ("content",),
    "SOAPNote": ("subjective", "objective", "assessment", "plan"),
    "ProgressNote": ("narrative",),
    "ProcedureNote": ("description",),
    "ConsultationNote": ("reason_for_consult", "recommendations"),
    "DischargeNote": ("instructions",),
}


def encrypt_notes(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.core.documents import models as m

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
                            setattr(row, name, val)  # re-save -> encrypt
                            dirty.append(name)
                    if dirty:
                        row.save(update_fields=[*dirty, "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cymed_documents", "0002_alter_clinicaldocument_content_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_notes, noop_reverse),
    ]
