"""
Data migration: encrypt existing cymed_hospital_anesthesia JSON PHI (plaintext from before the
field became EncryptedJSON).

Per-tenant. Idempotent (skips already-encrypted). Reverse no-op.
"""
from django.db import migrations

_TARGETS = {'AnesthesiaRecord': ('agents_used',)}


def encrypt_json(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.hospital.anesthesia import models as m

    for model_name, fields in _TARGETS.items():
        Model = getattr(m, model_name)
        tenant_ids = set(Model.objects.values_list("tenant_id", flat=True))
        for tid in tenant_ids:
            with tenant_context(tid):
                for row in Model.objects.filter(tenant_id=tid).iterator():
                    dirty = []
                    for name in fields:
                        val = getattr(row, name)
                        if val:  # non-empty dict / list
                            setattr(row, name, val)  # re-save -> encrypt
                            dirty.append(name)
                    if dirty:
                        row.save(update_fields=[*dirty, "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("cymed_hospital_anesthesia", "0005_alter_anesthesiarecord_agents_used")]
    operations = [migrations.RunPython(encrypt_json, noop_reverse)]
