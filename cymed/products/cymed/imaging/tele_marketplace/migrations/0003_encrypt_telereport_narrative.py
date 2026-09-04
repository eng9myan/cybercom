"""
Data migration: encrypt existing cymed_img_tele_marketplace PHI free-text (plaintext from before
the fields became EncryptedText).

Per-tenant. Idempotent. Reverse no-op.
"""
from django.db import migrations

_TARGETS = {'TeleReport': ('text', 'impressions')}


def encrypt_narrative(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.imaging.tele_marketplace import models as m

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
    dependencies = [("cymed_img_tele_marketplace", "0002_alter_telereport_impressions_alter_telereport_text")]
    operations = [migrations.RunPython(encrypt_narrative, noop_reverse)]
