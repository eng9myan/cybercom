"""
M-6 data migration: encrypt existing Patient.first_name / last_name / mrn
(plaintext from before those fields became EncryptedText) and populate the
companion *_bidx blind-index columns so exact-match lookup and the MRN
uniqueness constraint keep working.

Per-tenant (encryption needs the tenant context). Idempotent — an
already-encrypted value is re-saved harmlessly; a masked/undecryptable
sentinel is skipped. Reverse is a no-op (decryption on demand still works).
"""
from django.db import migrations

_SENTINELS = {"••••", "⚠ unavailable", ""}


def encrypt_names(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.core.patients.models import Patient

    tenant_ids = set(Patient.all_objects.values_list("tenant_id", flat=True)) \
        if hasattr(Patient, "all_objects") else set(Patient.objects.values_list("tenant_id", flat=True))

    for tid in tenant_ids:
        with tenant_context(tid):
            qs = (Patient.all_objects if hasattr(Patient, "all_objects") else Patient.objects)
            for row in qs.filter(tenant_id=tid).iterator():
                dirty = []
                for name in ("first_name", "last_name", "mrn"):
                    val = getattr(row, name)
                    if val and val not in _SENTINELS:
                        setattr(row, name, val)  # re-save -> encrypt + set <name>_bidx
                        dirty.append(name)
                if dirty:
                    bidx = [f"{n}_bidx" for n in dirty]
                    row.save(update_fields=[*dirty, *bidx, "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cymed_patients", "0007_alter_patient_options_patient_first_name_bidx_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_names, noop_reverse),
    ]
