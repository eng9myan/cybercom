"""
Seeds the single global default commission policy: 5%, applied to
gross-merchandise-value-after-merchant-discount, delivery and tips
excluded — exactly the CyberCom master spec section 8 default. This row
IS the "default 5%" — CommissionEngine has no hardcoded percentage
anywhere; if this migration hasn't run, resolve_policy() raises rather
than silently assuming a rate.
"""

from decimal import Decimal

from django.db import migrations
from django.utils import timezone


def seed_global_policy(apps, schema_editor):
    CommissionPolicy = apps.get_model("cymart_commission", "CommissionPolicy")
    if CommissionPolicy.objects.filter(scope="global").exists():
        return
    CommissionPolicy.objects.create(
        scope="global",
        scope_ref_id=None,
        commission_base="gross_after_merchant_discount",
        percentage=Decimal("5.00"),
        fixed_fee=Decimal("0.00"),
        delivery_excluded=True,
        tips_excluded=True,
        taxes_included=False,
        is_exempt=False,
        requires_approval=False,
        approved=True,
        effective_from=timezone.now(),
    )


def remove_global_policy(apps, schema_editor):
    CommissionPolicy = apps.get_model("cymart_commission", "CommissionPolicy")
    CommissionPolicy.objects.filter(scope="global", percentage=Decimal("5.00")).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cymart_commission", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_global_policy, remove_global_policy),
    ]
