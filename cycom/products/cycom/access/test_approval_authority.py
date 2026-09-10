"""HR-4 — value-based approval enforcement on PO / payment approve actions."""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from platform.provisioning.models import ApprovalPolicy, ApprovalTier
from products.cycom.access.approvals import (
    required_approver_role,
    require_approval_authority,
)
from products.cycom.access.models import Role, RoleAssignment
from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, Partner, Payment
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine


def _policy(tenant_id, doc_type="purchase_request"):
    p = ApprovalPolicy.objects.create(
        tenant_id=tenant_id, document_type=doc_type, name=f"{doc_type} approval"
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=p, sequence=1,
        threshold_min=0, threshold_max=500, approver_role="Department Manager",
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=p, sequence=2,
        threshold_min=500, threshold_max=5000, approver_role="Procurement Manager",
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=p, sequence=3,
        threshold_min=5000, threshold_max=None, approver_role="General Manager",
    )
    return p


class _Req:
    """Minimal stand-in for a DRF request in unit tests."""

    def __init__(self, roles=(), sub=None, tenant_id=None):
        self.auth_claims = {"sub": sub, "realm_access": {"roles": list(roles)}}
        self.user_session = {"user_id": sub, "roles": list(roles)}
        self.tenant_id = tenant_id


# ── tier resolution ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_required_role_follows_the_amount_band():
    t = uuid.uuid4()
    _policy(t)
    assert required_approver_role(t, "purchase_request", Decimal("100")) == "Department Manager"
    assert required_approver_role(t, "purchase_request", Decimal("500")) == "Procurement Manager"
    assert required_approver_role(t, "purchase_request", Decimal("4999")) == "Procurement Manager"
    assert required_approver_role(t, "purchase_request", Decimal("5000")) == "General Manager"
    assert required_approver_role(t, "purchase_request", Decimal("9_000_000")) == "General Manager"


@pytest.mark.django_db
def test_no_policy_returns_none():
    assert required_approver_role(uuid.uuid4(), "purchase_request", 100) is None


@pytest.mark.django_db
def test_purchase_order_falls_back_to_purchase_request_policy():
    t = uuid.uuid4()
    _policy(t, "purchase_request")
    assert required_approver_role(t, "purchase_order", Decimal("300")) == "Department Manager"


# ── authority check ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_no_policy_requires_admin():
    t = uuid.uuid4()
    with pytest.raises(Exception):
        require_approval_authority(_Req(roles=["buyer"], sub="u1"), t, "purchase_request", 100)
    # admin passes
    require_approval_authority(_Req(roles=["tenant_admin"], sub="a1"), t, "purchase_request", 100)


@pytest.mark.django_db
def test_authority_matches_the_band_role_from_token_claim():
    t = uuid.uuid4()
    _policy(t)
    # 300 -> Department Manager band
    require_approval_authority(_Req(roles=["Department Manager"], sub="u1"), t, "purchase_request", 300)
    # a Department Manager cannot approve a 2000 (Procurement Manager) request
    with pytest.raises(Exception):
        require_approval_authority(_Req(roles=["Department Manager"], sub="u1"), t, "purchase_request", 2000)
    require_approval_authority(_Req(roles=["procurement_manager"], sub="u2"), t, "purchase_request", 2000)


@pytest.mark.django_db
def test_authority_matches_provisioned_role_assignment():
    t = uuid.uuid4()
    _policy(t)
    role = Role.objects.create(tenant_id=t, name="Procurement Manager")
    RoleAssignment.objects.create(tenant_id=t, user_id="user-42", role=role)
    require_approval_authority(_Req(sub="user-42"), t, "purchase_request", 1200)
    with pytest.raises(Exception):
        require_approval_authority(_Req(sub="nobody"), t, "purchase_request", 1200)


# ── API wiring ──────────────────────────────────────────────────────────────
def _client(mint_token, mock_jwks, tenant_id, roles, sub=None):
    sub = sub or str(uuid.uuid4())
    token = mint_token({
        "sub": sub, "email": "u@cybercom.io",
        "tenant_id": str(tenant_id), "realm_access": {"roles": roles},
    })
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return c


@pytest.fixture
def po(db, tenant_id):
    offset = Account.objects.create(tenant_id=tenant_id, code="1300", name="GRNI", account_type="asset")
    inv = Account.objects.create(tenant_id=tenant_id, code="1200", name="Inv", account_type="asset")
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")
    vendor = Partner.objects.create(tenant_id=tenant_id, name="Vendor", partner_type="vendor")
    prod = Product.objects.create(tenant_id=tenant_id, sku="S1", name="Widget", inventory_account=inv)
    order = PurchaseOrder.objects.create(tenant_id=tenant_id, vendor=vendor, warehouse=wh, status="draft")
    PurchaseOrderLine.objects.create(
        tenant_id=tenant_id, order=order, product=prod,
        quantity=Decimal("10"), unit_cost=Decimal("120"), offset_account=offset,
    )  # total 1200 -> Procurement Manager band
    return order


@pytest.mark.django_db
def test_po_approve_blocks_wrong_role_and_allows_right_role(po, tenant_id, mint_token, mock_jwks):
    _policy(tenant_id)

    buyer = _client(mint_token, mock_jwks, tenant_id, ["Buyer"])
    r = buyer.post(f"/api/v1/procurement/orders/{po.id}/approve/")
    assert r.status_code == 403, r.content
    po.refresh_from_db()
    assert po.status == "draft"

    mgr = _client(mint_token, mock_jwks, tenant_id, ["Procurement Manager"])
    r = mgr.post(f"/api/v1/procurement/orders/{po.id}/approve/")
    assert r.status_code == 200, r.content
    po.refresh_from_db()
    assert po.status == "approved"


@pytest.mark.django_db
def test_po_approve_still_works_for_admin_without_policy(po, tenant_id, mint_token, mock_jwks):
    admin = _client(mint_token, mock_jwks, tenant_id, ["platform_admin"])
    r = admin.post(f"/api/v1/procurement/orders/{po.id}/approve/")
    assert r.status_code == 200, r.content


@pytest.mark.django_db
def test_vendor_payment_post_is_approval_gated(tenant_id, mint_token, mock_jwks):
    _policy(tenant_id, "payment")
    ApprovalTier.objects.filter(policy__tenant_id=tenant_id, policy__document_type="payment").delete()
    pol = ApprovalPolicy.objects.get(tenant_id=tenant_id, document_type="payment")
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=pol, sequence=1,
        threshold_min=0, threshold_max=None, approver_role="Finance Manager",
    )

    control = Account.objects.create(tenant_id=tenant_id, code="2100", name="AP", account_type="liability")
    exp = Account.objects.create(tenant_id=tenant_id, code="5000", name="Exp", account_type="expense")
    cash = Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset")
    vendor = Partner.objects.create(tenant_id=tenant_id, name="V", partner_type="vendor")
    bill = Invoice.objects.create(
        tenant_id=tenant_id, invoice_type="vendor", number="BILL-1", partner=vendor,
        date="2026-02-01", due_date="2026-03-01", control_account=control,
        amount_subtotal=Decimal("100"), amount_tax=0, amount_total=Decimal("100"), status="posted",
    )
    pay = Payment.objects.create(
        tenant_id=tenant_id, partner=vendor, invoice=bill, cash_account=cash,
        amount=Decimal("100"), date="2026-02-10", method="bank",
    )

    clerk = _client(mint_token, mock_jwks, tenant_id, ["Accountant"])
    r = clerk.post(f"/api/v1/ar-ap/payments/{pay.id}/post/")
    assert r.status_code == 403, r.content

    fin = _client(mint_token, mock_jwks, tenant_id, ["Finance Manager"])
    r = fin.post(f"/api/v1/ar-ap/payments/{pay.id}/post/")
    assert r.status_code == 200, r.content
