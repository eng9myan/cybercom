"""
Data migration: encrypt existing HakeemMessage.subject_national_id (plaintext
from before the field became EncryptedText) and populate the blind index.

Per-tenant (encryption needs the tenant context). Idempotent — an already-
encrypted value is left alone. Reverse is a no-op.
"""
from django.db import migrations


def encrypt_ids(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cymed.integrations.hakeem.models import HakeemMessage

    tenant_ids = set(HakeemMessage.objects.values_list("tenant_id", flat=True))
    for tid in tenant_ids:
        with tenant_context(tid):
            for msg in HakeemMessage.objects.filter(tenant_id=tid).iterator():
                val = msg.subject_national_id
                if val and val != "••••":
                    msg.subject_national_id = val  # re-save -> encrypt + set _bidx
                    msg.save(update_fields=["subject_national_id",
                                            "subject_national_id_bidx", "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cymed_int_hakeem", "0002_hakeemmessage_subject_national_id_bidx_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_ids, noop_reverse),
    ]
