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
    }


def _make_order(tenant_id, fixtures, discount_percent):
    order = POSOrder.objects.create(
        tenant_id=tenant_id,
        session=fixtures["session"],
        order_number=f"POS-{uuid.uuid4().hex[:8]}",
        cash_account=fixtures["cash_account"],
        revenue_account=fixtures["revenue_account"],
        cogs_account=fixtures["cogs_account"],
    )
    POSOrderLine.objects.create(
        tenant_id=tenant_id,
        order=order,
        product=fixtures["product"],
        quantity=Decimal("2"),
        unit_price=Decimal("50"),
        discount_percent=Decimal(str(discount_percent)),
    )
    return order


@pytest.mark.django_db
def test_checkout_blocked_when_discount_exceeds_threshold_unapproved(platform_admin_client, pos_fixtures):
    client, tenant_id = platform_admin_client
    order = _make_order(tenant_id, pos_fixtures, discount_percent=25)

    resp = client.post(f"/api/v1/pos/orders/{order.id}/checkout/")
    assert resp.status_code == 400
    assert "discount" in str(resp.data).lower()

    order.refresh_from_db()
    assert order.status == "draft"


@pytest.mark.django_db
def test_checkout_allowed_under_threshold_no_approval_needed(platform_admin_client, pos_fixtures):
    client, tenant_id = platform_admin_client
    order = _make_order(tenant_id, pos_fixtures, discount_percent=5)

    resp = client.post(f"/api/v1/pos/orders/{order.id}/checkout/")
    assert resp.status_code == 200
    order.refresh_from_db()
    assert order.status == "paid"
    # 2 * 50 * 0.95 = 95
    assert order.amount_subtotal == Decimal("95.00")


@pytest.mark.django_db
def test_submit_approve_then_checkout_succeeds(platform_admin_client, pos_fixtures):
    client, tenant_id = platform_admin_client
    order = _make_order(tenant_id, pos_fixtures, discount_percent=30)

    submit_resp = client.post(f"/api/v1/pos/orders/{order.id}/submit-discount/")
    assert submit_resp.status_code == 200
    order.refresh_from_db()
    assert order.discount_approval_status == "pending"

    approve_resp = client.post(f"/api/v1/pos/orders/{order.id}/approve-discount/")
    assert approve_resp.status_code == 200
    order.refresh_from_db()
    assert order.discount_approval_status == "approved"
    assert order.discount_approved_by == "admin@cybercom.io"

    checkout_resp = client.post(f"/api/v1/pos/orders/{order.id}/checkout/")
    assert checkout_resp.status_code == 200
    order.refresh_from_db()
    assert order.status == "paid"
    # 2 * 50 * 0.70 = 70
    assert order.amount_subtotal == Decimal("70.00")


@pytest.mark.django_db
def test_reject_discount_keeps_checkout_blocked(platform_admin_client, pos_fixtures):
    client, tenant_id = platform_admin_client
    order = _make_order(tenant_id, pos_fixtures, discount_percent=40)

    client.post(f"/api/v1/pos/orders/{order.id}/submit-discount/")
    reject_resp = client.post(
        f"/api/v1/pos/orders/{order.id}/reject-discount/", {"reason": "too steep"}, format="json"
    )
    assert reject_resp.status_code == 200
    order.refresh_from_db()
    assert order.discount_approval_status == "rejected"
    assert order.discount_rejection_reason == "too steep"

    checkout_resp = client.post(f"/api/v1/pos/orders/{order.id}/checkout/")
    assert checkout_resp.status_code == 400


@pytest.mark.django_db
def test_non_admin_cannot_approve_discount(mint_token, mock_jwks, tenant_id, pos_fixtures):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "cashier@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": []},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    order = _make_order(tenant_id, pos_fixtures, discount_percent=40)
    client.post(f"/api/v1/pos/orders/{order.id}/submit-discount/")
    resp = client.post(f"/api/v1/pos/orders/{order.id}/approve-discount/")
    assert resp.status_code == 403
