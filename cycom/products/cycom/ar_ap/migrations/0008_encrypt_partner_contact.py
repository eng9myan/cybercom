"""
Data migration: encrypt existing Partner.email / phone / contact_name / address
(plaintext from before the fields became EncryptedText) and populate email_bidx.

Per-tenant (encryption needs the tenant context). Idempotent — an already-
encrypted value is left alone. Reverse is a no-op.
"""
from django.db import migrations

_FIELDS = ("email", "phone", "contact_name", "address")


def encrypt_contact(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cycom.ar_ap.models import Partner

    tenant_ids = set(Partner.objects.values_list("tenant_id", flat=True))
    for tid in tenant_ids:
        with tenant_context(tid):
            for p in Partner.objects.filter(tenant_id=tid).iterator():
                dirty = []
                for name in _FIELDS:
                    val = getattr(p, name)
                    if val and val != "••••":
                        setattr(p, name, val)  # re-save -> encrypt (+ email_bidx)
                        dirty.append(name)
                if dirty:
                    if "email" in dirty:
                        dirty.append("email_bidx")
                    p.save(update_fields=[*dirty, "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cycom_ar_ap", "0007_partner_email_bidx_alter_partner_address_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_contact, noop_reverse),
    ]
