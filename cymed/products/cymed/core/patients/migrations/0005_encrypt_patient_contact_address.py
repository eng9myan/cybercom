"""
Data migration: encrypt existing PatientContact.telecom_value and
PatientAddress.line1 / line2 / postal_code (plaintext from before the fields
became EncryptedText).

Per-tenant (encryption needs the tenant context). Idempotent — an
already-encrypted value is left alone. Reverse is a no-op.
"""
from django.db import migrations


def encrypt_contacts(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.core.patients.models import PatientAddress, PatientContact

    for model, field_names in (
        (PatientContact, ("telecom_value",)),
        (PatientAddress, ("line1", "line2", "postal_code")),
    ):
        tenant_ids = set(model.objects.values_list("tenant_id", flat=True))
        for tid in tenant_ids:
            with tenant_context(tid):
                for row in model.objects.filter(tenant_id=tid).iterator():
                    dirty = []
                    for name in field_names:
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
        ("cymed_patients", "0004_alter_patientaddress_line1_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_contacts, noop_reverse),
    ]
