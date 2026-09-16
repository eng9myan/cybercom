"""Phase 2 retail verticals at the POS checkout money-path: weight-based
pricing (Grocery / Sweets & Bakery — fractional quantity, existing
quantity*unit_price math) and serial-tracked checkout (Electronics — a line
must name exactly `quantity` serials, which flip to 'issued' on checkout)."""

import uuid
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.models import Account
from products.cycom.catalog.models import Product
from products.cycom.inventory.models import SerialUnit, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.pos.models import POSOrder, POSOrderLine, POSSession
from products.cycom.pos.serializers import POSOrderLineSerializer
from products.cycom.pos.services import checkout_order


@pytest.fixture
def shop(db, tenant_id):
    inv_acct = Account.objects.create(tenant_id=tenant_id, code="1140", name="Inventory", account_type="asset")
    accounts = dict(
        cash=Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset"),
        revenue=Account.objects.create(tenant_id=tenant_id, code="4000", name="Revenue", account_type="income"),
        cogs=Account.objects.create(tenant_id=tenant_id, code="5000", name="COGS", account_type="expense"),
    )
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH", name="Main")
    return {"a": accounts, "wh": wh, "inv_acct": inv_acct}


def _session_and_order(tenant_id, shop):
    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=shop["wh"])
    return POSOrder.objects.create(
        tenant_id=tenant_id, session=session, order_number=f"POS-{uuid.uuid4().hex[:8]}",
        cash_account=shop["a"]["cash"], revenue_account=shop["a"]["revenue"],
        cogs_account=shop["a"]["cogs"], currency="JOD",
    )


# ── Weight-based pricing ─────────────────────────────────────────────────────
@pytest.mark.django_db
def test_weight_mode_line_math_and_serializer_surface(tenant_id, shop):
    cheese = Product.objects.create(
        tenant_id=tenant_id, name="Halloumi (bulk)", internal_ref="CHEESE-BULK",
        pricing_mode="weight", inventory_account=shop["inv_acct"],
    )
    rcpt = StockMove.objects.create(
        tenant_id=tenant_id, move_type="receipt", product=cheese, warehouse=shop["wh"],
        quantity=Decimal("50"), unit_cost=Decimal("3.00"), date="2026-01-01",
        offset_account=shop["a"]["cash"], status="draft",
    )
    apply_stock_move(rcpt)

    order = _session_and_order(tenant_id, shop)
    # 0.375 kg @ 8.00 JOD/kg
    line = POSOrderLine.objects.create(
        tenant_id=tenant_id, order=order, product=cheese,
        quantity=Decimal("0.375"), unit_price=Decimal("8.00"),
    )
    assert line.subtotal == Decimal("3.00")

    data = POSOrderLineSerializer(line).data
    assert data["pricing_mode"] == "weight"

    checkout_order(order)
    order.refresh_from_db()
    assert order.status == "paid"
    assert order.amount_subtotal == Decimal("3.00")


# ── Serial-tracked checkout ──────────────────────────────────────────────────
@pytest.fixture
def serial_shop(tenant_id, shop):
    tv = Product.objects.create(
        tenant_id=tenant_id, name="4K TV 55in", internal_ref="TV-55-4K",
        tracking_mode="serial", inventory_account=shop["inv_acct"],
    )
    rcpt = StockMove.objects.create(
        tenant_id=tenant_id, move_type="receipt", product=tv, warehouse=shop["wh"],
        quantity=Decimal("2"), unit_cost=Decimal("300"), date="2026-01-01",
        offset_account=shop["a"]["cash"], status="draft",
        serial_numbers=["SN-100", "SN-101"],
    )
    apply_stock_move(rcpt)
    return {**shop, "product": tv}


@pytest.mark.django_db
def test_serial_checkout_requires_matching_serials_on_the_line(tenant_id, serial_shop):
    order = _session_and_order(tenant_id, serial_shop)
    POSOrderLine.objects.create(
        tenant_id=tenant_id, order=order, product=serial_shop["product"],
        quantity=Decimal("1"), unit_price=Decimal("450"),
    )  # no serial_numbers supplied
    with pytest.raises(ValidationError):
        checkout_order(order)


@pytest.mark.django_db
def test_serial_checkout_issues_the_named_unit(tenant_id, serial_shop):
    order = _session_and_order(tenant_id, serial_shop)
    POSOrderLine.objects.create(
        tenant_id=tenant_id, order=order, product=serial_shop["product"],
        quantity=Decimal("1"), unit_price=Decimal("450"), serial_numbers=["SN-100"],
    )
    checkout_order(order)
    order.refresh_from_db()
    assert order.status == "paid"

    sold = SerialUnit.objects.get(tenant_id=tenant_id, serial_number="SN-100")
    assert sold.status == "issued"
    still_in_stock = SerialUnit.objects.get(tenant_id=tenant_id, serial_number="SN-101")
    assert still_in_stock.status == "in_stock"
