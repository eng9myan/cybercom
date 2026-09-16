"""S-2 — POS order GL accounts resolve from the branch (warehouse) config
instead of demanding chart-of-accounts UUIDs in every checkout request."""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.pos.models import POSSession


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "admin@cybercom.io",
        "tenant_id": str(tenant_id), "realm_access": {"roles": ["platform_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def accounts(db, tenant_id):
    return {
        "cash": Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset"),
        "rev": Account.objects.create(tenant_id=tenant_id, code="4000", name="Sales", account_type="income"),
        "cogs": Account.objects.create(tenant_id=tenant_id, code="5000", name="COGS", account_type="expense"),
        "inv": Account.objects.create(tenant_id=tenant_id, code="1200", name="Inventory", account_type="asset"),
    }


def _order_payload(session, product):
    return {
        "session": str(session.id),
        "lines": [{"product": str(product.id), "quantity": "1", "unit_price": "10"}],
    }


@pytest.mark.django_db
def test_order_resolves_accounts_from_configured_branch(admin_client, tenant_id, accounts):
    wh = Warehouse.objects.create(
        tenant_id=tenant_id, code="WH-BR1", name="Branch 1",
        pos_cash_account=accounts["cash"], pos_revenue_account=accounts["rev"],
        pos_cogs_account=accounts["cogs"],
    )
    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=wh, opening_cash=0)
    product = Product.objects.create(
        tenant_id=tenant_id, internal_ref="S1", name="Widget", inventory_account=accounts["inv"]
    )

    resp = admin_client.post("/api/v1/pos/orders/", _order_payload(session, product), format="json")
    assert resp.status_code == 201, resp.content
    assert str(resp.data["cash_account"]) == str(accounts["cash"].id)
    assert str(resp.data["revenue_account"]) == str(accounts["rev"].id)
    assert str(resp.data["cogs_account"]) == str(accounts["cogs"].id)


@pytest.mark.django_db
def test_order_still_accepts_explicit_override_over_branch_default(admin_client, tenant_id, accounts):
    wh = Warehouse.objects.create(
        tenant_id=tenant_id, code="WH-BR2", name="Branch 2",
        pos_cash_account=accounts["cash"], pos_revenue_account=accounts["rev"],
        pos_cogs_account=accounts["cogs"],
    )
    other_cash = Account.objects.create(tenant_id=tenant_id, code="1010", name="Petty Cash", account_type="asset")
    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=wh, opening_cash=0)
    product = Product.objects.create(
        tenant_id=tenant_id, internal_ref="S2", name="Gadget", inventory_account=accounts["inv"]
    )

    payload = _order_payload(session, product)
    payload["cash_account"] = str(other_cash.id)
    resp = admin_client.post("/api/v1/pos/orders/", payload, format="json")
    assert resp.status_code == 201, resp.content
    assert str(resp.data["cash_account"]) == str(other_cash.id)
    assert str(resp.data["revenue_account"]) == str(accounts["rev"].id)  # unconfigured field still defaults


@pytest.mark.django_db
def test_order_rejects_cleanly_when_branch_has_no_config_and_none_supplied(admin_client, tenant_id, accounts):
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH-BR3", name="Branch 3")  # no POS config
    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=wh, opening_cash=0)
    product = Product.objects.create(
        tenant_id=tenant_id, internal_ref="S3", name="Gizmo", inventory_account=accounts["inv"]
    )

    resp = admin_client.post("/api/v1/pos/orders/", _order_payload(session, product), format="json")
    assert resp.status_code == 400
    detail = str(resp.data)
    for field in ("cash_account", "revenue_account", "cogs_account"):
        assert field in detail
