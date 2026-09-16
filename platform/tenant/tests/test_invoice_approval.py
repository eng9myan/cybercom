"""Admin invoice-approval API (audit follow-up): activate_paid_subscription()
existed with no human-reachable path for the manual/bank-transfer case —
finance had no button to confirm a payment landed. TenantSubscriptionInvoiceViewSet
+ its mark-paid action close that gap."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import (
    InvoiceStatus,
    SubscriptionPlan,
    Tenant,
    TenantStatus,
    TenantSubscription,
    TenantSubscriptionInvoice,
    TenantType,
)


def _make_invoice(status=InvoiceStatus.PENDING):
    suffix = uuid.uuid4().hex[:8]
    tenant = Tenant.objects.create(
        name=f"Acme {suffix}", slug=f"acme-{suffix}",
        tenant_type=TenantType.SAAS, status=TenantStatus.PENDING,
    )
    sub = TenantSubscription.objects.create(
        tenant=tenant, plan=SubscriptionPlan.PROFESSIONAL, is_active=False,
    )
    inv = TenantSubscriptionInvoice.objects.create(
        subscription=sub, invoice_number=f"INV-{suffix}", amount=Decimal("149.00"),
        currency="USD", due_date=date.today() + timedelta(days=7), status=status,
    )
    return tenant, sub, inv


def _authed_client(mint_token, mock_jwks, *, roles, tenant_id=None, email="admin@cybercom.io"):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": email,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "realm_access": {"roles": roles},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestInvoiceApprovalAPI:
    def test_platform_admin_marks_invoice_paid_and_activates_tenant(self, mint_token, mock_jwks):
        tenant, sub, inv = _make_invoice()
        client = _authed_client(
            mint_token, mock_jwks, roles=["platform_admin"], email="finance@cybercom.io"
        )

        resp = client.post(f"/api/v1/tenants/subscription-invoices/{inv.id}/mark-paid/")
        assert resp.status_code == 200, resp.content

        inv.refresh_from_db(); tenant.refresh_from_db(); sub.refresh_from_db()
        assert inv.status == InvoiceStatus.PAID
        assert inv.approved_by == "manual:finance@cybercom.io"
        assert tenant.status == TenantStatus.ACTIVE
        assert sub.is_active is True

    def test_tenant_admin_cannot_mark_paid(self, mint_token, mock_jwks):
        tenant, _, inv = _make_invoice()
        client = _authed_client(mint_token, mock_jwks, roles=["tenant_admin"], tenant_id=tenant.id)

        resp = client.post(f"/api/v1/tenants/subscription-invoices/{inv.id}/mark-paid/")
        assert resp.status_code == 403

        inv.refresh_from_db()
        assert inv.status == InvoiceStatus.PENDING

    def test_already_paid_invoice_rejects_double_approval(self, mint_token, mock_jwks):
        _, _, inv = _make_invoice(status=InvoiceStatus.PAID)
        client = _authed_client(mint_token, mock_jwks, roles=["platform_admin"])

        resp = client.post(f"/api/v1/tenants/subscription-invoices/{inv.id}/mark-paid/")
        assert resp.status_code == 400

    def test_tenant_only_sees_its_own_invoices(self, mint_token, mock_jwks):
        tenant_a, _, inv_a = _make_invoice()
        _, _, inv_b = _make_invoice()
        client = _authed_client(mint_token, mock_jwks, roles=["tenant_admin"], tenant_id=tenant_a.id)

        resp = client.get("/api/v1/tenants/subscription-invoices/")
        assert resp.status_code == 200, resp.content
        body = resp.json()
        rows = body["results"] if isinstance(body, dict) else body
        ids = {row["id"] for row in rows}
        assert str(inv_a.id) in ids
        assert str(inv_b.id) not in ids

    def test_platform_admin_sees_all_invoices(self, mint_token, mock_jwks):
        _, _, inv_a = _make_invoice()
        _, _, inv_b = _make_invoice()
        client = _authed_client(mint_token, mock_jwks, roles=["platform_admin"])

        resp = client.get("/api/v1/tenants/subscription-invoices/")
        assert resp.status_code == 200, resp.content
        body = resp.json()
        rows = body["results"] if isinstance(body, dict) else body
        ids = {row["id"] for row in rows}
        assert {str(inv_a.id), str(inv_b.id)} <= ids

    def test_unauthenticated_request_rejected(self):
        _, _, inv = _make_invoice()
        client = APIClient()
        resp = client.post(f"/api/v1/tenants/subscription-invoices/{inv.id}/mark-paid/")
        assert resp.status_code == 401
