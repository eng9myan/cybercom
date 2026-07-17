import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.pos.models import POSOrder, POSOrderLine, POSSession


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, tenant_id


@pytest.fixture
def pos_fixtures(db, tenant_id):
    inventory_account = Account.objects.create(
        tenant_id=tenant_id, code="1200", name="Inventory", account_type="asset"
    )
    cash_account = Account.objects.create(
        tenant_id=tenant_id, code="1000", name="Cash", account_type="asset"
    )
    revenue_account = Account.objects.create(
        tenant_id=tenant_id, code="4000", name="Sales Revenue", account_type="income"
    )
    cogs_account = Account.objects.create(
        tenant_id=tenant_id, code="5000", name="COGS", account_type="expense"
    )
    advance_liability_account = Account.objects.create(
        tenant_id=tenant_id, code="2200", name="Customer Deposits", account_type="liability"
    )
    warehouse = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main Warehouse")
    product = Product.objects.create(
        tenant_id=tenant_id, sku="SKU-1", name="Widget", inventory_account=inventory_account
    )

    receipt = StockMove.objects.create(
        tenant_id=tenant_id,
        move_type="receipt",
        product=product,
        warehouse=warehouse,
        quantity=Decimal("100"),
        unit_cost=Decimal("10"),
        date="2026-07-17",
        reference="INIT-STOCK",
        offset_account=cogs_account,
        status="draft",
    )
    apply_stock_move(receipt)

    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=warehouse, cashier="tester")

    return {
        "warehouse": warehouse,
        "product": product,
        "session": session,
        "cash_account": cash_account,
        "revenue_account": revenue_account,
        "cogs_account": cogs_account,
        "advance_liability_account": advance_liability_account,
    }


def _make_layaway_order(tenant_id, fixtures):
    order = POSOrder.objects.create(
        tenant_id=tenant_id,
        session=fixtures["session"],
        order_number=f"POS-{uuid.uuid4().hex[:8]}",
        order_type="layaway",
        cash_account=fixtures["cash_account"],
        revenue_account=fixtures["revenue_account"],
        cogs_account=fixtures["cogs_account"],
        advance_liability_account=fixtures["advance_liability_account"],
    )
    POSOrderLine.objects.create(
        tenant_id=tenant_id,
        order=order,
        product=fixtures["product"],
        quantity=Decimal("2"),
        unit_price=Decimal("50"),
    )
    return order


@pytest.mark.django_db
def test_checkout_blocked_until_fully_paid(platform_admin_client, pos_fixtures):
    client, tenant_id = platform_admin_client
    order = _make_layaway_order(tenant_id, pos_fixtures)

    pay_resp = client.post(
        f"/api/v1/pos/orders/{order.id}/add-payment/", {"amount": "40"}, format="json"
    )
    assert pay_resp.status_code == 200

    checkout_resp = client.post(f"/api/v1/pos/orders/{order.id}/checkout/")
    assert checkout_resp.status_code == 400
    assert "balance" in str(checkout_resp.data).lower()

    order.refresh_from_db()
    assert order.status == "draft"
    assert order.amount_paid == Decimal("40.00")


@pytest.mark.django_db
def test_multiple_advances_then_checkout_settles(platform_admin_client, pos_fixtures):
    client, tenant_id = platform_admin_client
    order = _make_layaway_order(tenant_id, pos_fixtures)
    # total = 2 * 50 = 100, no tax on these lines.

    client.post(f"/api/v1/pos/orders/{order.id}/add-payment/", {"amount": "30"}, format="json")
    client.post(f"/api/v1/pos/orders/{order.id}/add-payment/", {"amount": "70"}, format="json")

    order.refresh_from_db()
    assert order.amount_paid == Decimal("100.00")
    assert order.payments.count() == 2

    checkout_resp = client.post(f"/api/v1/pos/orders/{order.id}/checkout/")
    assert checkout_resp.status_code == 200
    order.refresh_from_db()
    assert order.status == "paid"
    assert order.amount_total == Decimal("100.00")

    # Deposit liability must be fully reversed to zero on the journal side —
    # verify via the GL: liability debit (checkout) should equal the sum of
    # the two advance credits.
    from products.cycom.accounting.models import JournalLine

    liability_lines = JournalLine.objects.filter(account=order.advance_liability_account)
    total_debit = sum((l.debit for l in liability_lines), Decimal("0"))
    total_credit = sum((l.credit for l in liability_lines), Decimal("0"))
    assert total_debit == total_credit == Decimal("100.00")


@pytest.mark.django_db
def test_advance_payment_rejected_on_regular_sale(platform_admin_client, pos_fixtures):
    client, tenant_id = platform_admin_client
    order = POSOrder.objects.create(
        tenant_id=tenant_id,
        session=pos_fixtures["session"],
        order_number=f"POS-{uuid.uuid4().hex[:8]}",
        cash_account=pos_fixtures["cash_account"],
        revenue_account=pos_fixtures["revenue_account"],
        cogs_account=pos_fixtures["cogs_account"],
    )
    POSOrderLine.objects.create(
        tenant_id=tenant_id,
        order=order,
        product=pos_fixtures["product"],
        quantity=Decimal("1"),
        unit_price=Decimal("10"),
    )

    resp = client.post(f"/api/v1/pos/orders/{order.id}/add-payment/", {"amount": "5"}, format="json")
    assert resp.status_code == 400
    assert "layaway" in str(resp.data).lower()
