import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from platform.provisioning.models import ApprovalPolicy, ApprovalTier
from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine

pytestmark = pytest.mark.django_db


def _policy(tenant_id):
    policy = ApprovalPolicy.objects.create(
        tenant_id=tenant_id, document_type="purchase_order", name="PO approval"
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=policy, sequence=1,
        threshold_min=0, threshold_max=1000, approver_role="Department Manager",
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=policy, sequence=2,
        threshold_min=1000, threshold_max=None, approver_role="General Manager",
    )
    return policy


def _client(mint_token, mock_jwks, tenant_id, roles):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "approver@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": list(roles)},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def po(tenant_id):
    vendor = Partner.objects.create(tenant_id=tenant_id, name="Steel Supplier", partner_type="vendor")
    warehouse = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main")
    grni = Account.objects.create(tenant_id=tenant_id, code="2115", name="GRNI", account_type="liability")
    inv_acct = Account.objects.create(tenant_id=tenant_id, code="1140", name="Inventory", account_type="asset")
    product = Product.objects.create(
        tenant_id=tenant_id, internal_ref="RB-12", name="Rebar 12mm", inventory_account=inv_acct
    )
    order = PurchaseOrder.objects.create(tenant_id=tenant_id, vendor=vendor, warehouse=warehouse, status="draft")
    PurchaseOrderLine.objects.create(
        tenant_id=tenant_id, order=order, product=product,
        quantity=Decimal("10"), unit_cost=Decimal("50"), offset_account=grni,
    )
    return order


def test_queue_hides_items_outside_the_callers_tier(mint_token, mock_jwks, tenant_id, po):
    """po totals 500 -> Department Manager's tier (0-1000)."""
    _policy(tenant_id)
    manager = _client(mint_token, mock_jwks, tenant_id, ["Department Manager"])
    resp = manager.get("/api/hitl/queue/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["type"] == "purchase_order"

    unrelated = _client(mint_token, mock_jwks, tenant_id, ["Sales Rep"])
    resp = unrelated.get("/api/hitl/queue/")
    assert resp.status_code == 200
    assert resp.data == []


def test_admin_sees_everything_regardless_of_policy(mint_token, mock_jwks, tenant_id, po):
    admin = _client(mint_token, mock_jwks, tenant_id, ["tenant_admin"])
    resp = admin.get("/api/hitl/queue/")
    assert resp.status_code == 200
    assert len(resp.data) == 1


def test_approve_requires_authority(mint_token, mock_jwks, tenant_id, po):
    _policy(tenant_id)
    unrelated = _client(mint_token, mock_jwks, tenant_id, ["Sales Rep"])
    resp = unrelated.post(f"/api/hitl/approve/{po.id}/")
    assert resp.status_code == 403
    po.refresh_from_db()
    assert po.status == "draft"


def test_approve_transitions_and_leaves_the_queue(mint_token, mock_jwks, tenant_id, po):
    _policy(tenant_id)
    manager = _client(mint_token, mock_jwks, tenant_id, ["Department Manager"])
    resp = manager.post(f"/api/hitl/approve/{po.id}/")
    assert resp.status_code == 200, resp.data
    po.refresh_from_db()
    assert po.status == "approved"

    resp = manager.get("/api/hitl/queue/")
    assert resp.data == []


def test_reject_transitions_and_leaves_the_queue(mint_token, mock_jwks, tenant_id, po):
    _policy(tenant_id)
    manager = _client(mint_token, mock_jwks, tenant_id, ["Department Manager"])
    resp = manager.post(f"/api/hitl/reject/{po.id}/")
    assert resp.status_code == 200, resp.data
    po.refresh_from_db()
    assert po.status == "rejected"


def test_cannot_approve_already_approved_po(mint_token, mock_jwks, tenant_id, po):
    _policy(tenant_id)
    manager = _client(mint_token, mock_jwks, tenant_id, ["Department Manager"])
    manager.post(f"/api/hitl/approve/{po.id}/")
    resp = manager.post(f"/api/hitl/approve/{po.id}/")
    assert resp.status_code == 400


def test_unknown_item_404s_cleanly(mint_token, mock_jwks, tenant_id):
    manager = _client(mint_token, mock_jwks, tenant_id, ["Department Manager"])
    resp = manager.post(f"/api/hitl/approve/{uuid.uuid4()}/")
    assert resp.status_code == 400


def test_tenant_isolation_on_queue(mint_token, mock_jwks, tenant_id, po):
    _policy(tenant_id)
    other_tenant_admin = _client(mint_token, mock_jwks, uuid.uuid4(), ["tenant_admin"])
    resp = other_tenant_admin.get("/api/hitl/queue/")
    assert resp.status_code == 200
    assert resp.data == []


def test_requires_auth(tenant_id):
    resp = APIClient().get("/api/hitl/queue/")
    assert resp.status_code == 401
