"""
Data migration: encrypt existing Patient.national_id / passport_number
(plaintext from before the fields became EncryptedText) and populate the
blind-index columns used for dedup / MPI search.

Per-tenant (encryption needs the tenant context). Idempotent — get_prep_value
leaves an already-encrypted value alone. Reverse is a no-op.
"""
from django.db import migrations


def encrypt_ids(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.core.patients.models import Patient

    tenant_ids = set(Patient.objects.values_list("tenant_id", flat=True))
    for tid in tenant_ids:
        with tenant_context(tid):
            for p in Patient.objects.filter(tenant_id=tid).iterator():
                dirty = []
                for name in ("national_id", "passport_number"):
                    val = getattr(p, name)
                    if val and val != "••••":
                        setattr(p, name, val)  # re-save -> encrypt + set _bidx
                        dirty += [name, f"{name}_bidx"]
                if dirty:
                    p.save(update_fields=[*dirty, "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cymed_patients", "0002_patient_national_id_bidx_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_ids, noop_reverse),
    ]
