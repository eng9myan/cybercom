"""Pharmacy Retail — a requires_prescription line is hard-gated at checkout,
mirroring the serial_numbers pattern already built for Electronics."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.models import Account
from products.cycom.catalog.models import Product
from products.cycom.inventory.models import StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.pos.models import POSOrder, POSOrderLine, POSSession, Prescription
from products.cycom.pos.services import checkout_order


@pytest.fixture
def shop(db, tenant_id):
    inv_acct = Account.objects.create(tenant_id=tenant_id, code="1140", name="Inventory", account_type="asset")
    accounts = dict(
        cash=Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset"),
        revenue=Account.objects.create(tenant_id=tenant_id, code="4000", name="Revenue", account_type="income"),
        cogs=Account.objects.create(tenant_id=tenant_id, code="5000", name="COGS", account_type="expense"),
    )
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH", name="Pharmacy")
    return {"a": accounts, "wh": wh, "inv_acct": inv_acct}


@pytest.fixture
def rx_drug(tenant_id, shop):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Amoxicillin 500mg", internal_ref="RX-AMX",
        requires_prescription=True, inventory_account=shop["inv_acct"],
    )
    move = StockMove.objects.create(
        tenant_id=tenant_id, move_type="receipt", product=product, warehouse=shop["wh"],
        quantity=Decimal("50"), unit_cost=Decimal("1.00"), date="2026-01-01",
        offset_account=shop["a"]["cash"], status="draft",
    )
    apply_stock_move(move)
    return product


def _order(tenant_id, shop, product, *, prescription=None, qty=1):
    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=shop["wh"])
    order = POSOrder.objects.create(
        tenant_id=tenant_id, session=session, order_number=f"POS-{uuid.uuid4().hex[:8]}",
        cash_account=shop["a"]["cash"], revenue_account=shop["a"]["revenue"],
        cogs_account=shop["a"]["cogs"], currency="JOD",
    )
    POSOrderLine.objects.create(
        tenant_id=tenant_id, order=order, product=product,
        quantity=Decimal(qty), unit_price=Decimal("5.00"), prescription=prescription,
    )
    return order


@pytest.mark.django_db
def test_checkout_blocked_without_a_prescription(tenant_id, shop, rx_drug):
    order = _order(tenant_id, shop, rx_drug)
    with pytest.raises(ValidationError):
        checkout_order(order)


@pytest.mark.django_db
def test_checkout_succeeds_with_a_valid_prescription_and_consumes_a_refill(tenant_id, shop, rx_drug):
    rx = Prescription.objects.create(
        tenant_id=tenant_id, patient_name="Layla Haddad", date_issued=date.today(),
        refills_allowed=2, refills_used=0,
    )
    order = _order(tenant_id, shop, rx_drug, prescription=rx)
    checkout_order(order)
    order.refresh_from_db()
    assert order.status == "paid"

    rx.refresh_from_db()
    assert rx.refills_used == 1
    assert rx.refills_remaining == 1


@pytest.mark.django_db
def test_checkout_blocked_when_refills_exhausted(tenant_id, shop, rx_drug):
    rx = Prescription.objects.create(
        tenant_id=tenant_id, patient_name="Omar Nasser", date_issued=date.today(),
        refills_allowed=1, refills_used=1,
    )
    assert rx.refills_remaining == 0
    order = _order(tenant_id, shop, rx_drug, prescription=rx)
    with pytest.raises(ValidationError):
        checkout_order(order)


@pytest.mark.django_db
def test_non_prescription_product_checks_out_normally(tenant_id, shop):
    otc = Product.objects.create(
        tenant_id=tenant_id, name="Ibuprofen 200mg", internal_ref="OTC-IBU",
        inventory_account=shop["inv_acct"],
    )
    move = StockMove.objects.create(
        tenant_id=tenant_id, move_type="receipt", product=otc, warehouse=shop["wh"],
        quantity=Decimal("50"), unit_cost=Decimal("1.00"), date="2026-01-01",
        offset_account=shop["a"]["cash"], status="draft",
    )
    apply_stock_move(move)

    order = _order(tenant_id, shop, otc)
    checkout_order(order)
    order.refresh_from_db()
    assert order.status == "paid"
