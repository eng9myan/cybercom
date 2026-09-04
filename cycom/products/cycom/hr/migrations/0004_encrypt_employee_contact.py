"""
Data migration: encrypt existing Employee.email / phone (plaintext from before
the fields became EncryptedText) and populate email_bidx.

Per-tenant (encryption needs the tenant context). Idempotent — an already-
encrypted value is left alone. Reverse is a no-op.
"""
from django.db import migrations


def encrypt_contact(apps, schema_editor):
    from platform.common.tenant_context import tenant_context

    from products.cycom.hr.models import Employee

    tenant_ids = set(Employee.objects.values_list("tenant_id", flat=True))
    for tid in tenant_ids:
        with tenant_context(tid):
            for emp in Employee.objects.filter(tenant_id=tid).iterator():
                dirty = []
                for name in ("email", "phone"):
                    val = getattr(emp, name)
                    if val and val != "••••":
                        setattr(emp, name, val)  # re-save -> encrypt + set _bidx
                        dirty.append(name)
                if dirty:
                    if "email" in dirty:
                        dirty.append("email_bidx")
                    emp.save(update_fields=[*dirty, "updated_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cycom_hr", "0003_employee_email_bidx_alter_employee_email_and_more"),
    ]
    operations = [
        migrations.RunPython(encrypt_contact, noop_reverse),
    ]
