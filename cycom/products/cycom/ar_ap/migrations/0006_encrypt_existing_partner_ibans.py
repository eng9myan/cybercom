"""
Data migration: encrypt any plaintext Partner.iban left from before the field
became EncryptedText, and populate the iban_bidx blind index.

Runs per-tenant (encryption needs the tenant context). Idempotent — a row
already holding ciphertext is left alone by the field's get_prep_value.
Reverse is a no-op (decryption on read keeps working).
"""
from django.db import migrations


def encrypt_ibans(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    # Use the real model so EncryptedText's encrypt-on-save runs.
    from products.cycom.ar_ap.models import Partner

    seen_tenants = set()
    for pk, tid in Partner.objects.values_list("id", "tenant_id"):
        seen_tenants.add(tid)

    for tid in seen_tenants:
        with tenant_context(tid):
            for row in Partner.objects.filter(tenant_id=tid).iterator():
                val = row.iban  # decoded plaintext or decrypted ciphertext
                if not val or val == "••••":
                    continue
                row.iban = val  # re-save -> get_prep_value encrypts, pre_save sets bidx
                row.save(update_fields=["iban", "iban_bidx", "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cycom_ar_ap", "0005_partner_iban_bidx_alter_partner_iban"),
    ]
    operations = [
        migrations.RunPython(encrypt_ibans, noop_reverse),
    ]
