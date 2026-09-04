"""
Money-path tests for sales quotations / orders — the app had zero test coverage.

Covers the line arithmetic (subtotal, discount, tax), header roll-up
(`recompute_totals`), and the retail vs wholesale customer-type split that was
ported from CyShop. See docs/blueprint/LAUNCH_READINESS.md §5.
"""
from decimal import Decimal

import pytest

from products.cycom.sales.models import SalesOrder, SalesOrderLine

T = "11111111-1111-1111-1111-111111111111"


@pytest.mark.django_db
def test_line_subtotal_applies_discount_then_tax():
    order = SalesOrder.objects.create(
        tenant_id=T, number="Q-1", customer_name="Acme", order_date="2026-07-01",
    )
    line = SalesOrderLine.objects.create(
        tenant_id=T, order=order, description="Widget",
        quantity=Decimal("10"), unit_price=Decimal("5.00"),
        discount_percent=Decimal("10"), tax_percent=Decimal("16"),
    )
    # 10 x 5.00 = 50.00, less 10% = 45.00, tax 16% = 7.20
    assert line.subtotal == Decimal("45.00")
    assert line.tax_amount == Decimal("7.20")


@pytest.mark.django_db
def test_recompute_totals_rolls_up_lines():
    order = SalesOrder.objects.create(
        tenant_id=T, number="Q-2", customer_name="Acme", order_date="2026-07-01",
    )
    SalesOrderLine.objects.create(
        tenant_id=T, order=order, quantity=Decimal("2"), unit_price=Decimal("10.00"),
        tax_percent=Decimal("16"),
    )
    SalesOrderLine.objects.create(
        tenant_id=T, order=order, quantity=Decimal("1"), unit_price=Decimal("30.00"),
        tax_percent=Decimal("0"),
    )
    order.recompute_totals()
    order.refresh_from_db()
    # 20.00 + 30.00 subtotal; tax only on the first line: 3.20
    assert order.amount_subtotal == Decimal("50.00")
    assert order.amount_tax == Decimal("3.20")
    assert order.amount_total == Decimal("53.20")
    # header tax == sum of line taxes
    assert order.amount_tax == sum((l.tax_amount for l in order.lines.all()), Decimal("0"))


@pytest.mark.django_db
def test_customer_type_defaults_retail_and_accepts_wholesale():
    retail = SalesOrder.objects.create(
        tenant_id=T, number="Q-3", customer_name="Walk-in", order_date="2026-07-01",
    )
    assert retail.customer_type == "retail"

    wholesale = SalesOrder.objects.create(
        tenant_id=T, number="Q-4", customer_name="Distributor",
        order_date="2026-07-01", customer_type="wholesale",
    )
    assert wholesale.customer_type == "wholesale"


@pytest.mark.django_db
def test_zero_line_order_rolls_up_to_zero():
    order = SalesOrder.objects.create(
        tenant_id=T, number="Q-5", customer_name="Acme", order_date="2026-07-01",
    )
    order.recompute_totals()
    order.refresh_from_db()
    assert order.amount_subtotal == order.amount_tax == order.amount_total == Decimal("0.00")
