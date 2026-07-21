"""
CyID ecosystem, Phase 6 — real per-country e-invoicing routing when an
invoice is posted. Jurisdiction is derived from the tenant's own
platform.tenant.Tenant.country_code (already real, no new Invoice field),
region sent to compliance-gateway is exactly what
compliance-gateway/main.py's process_fiscal_compliance() switches on.
"""

import uuid
from datetime import date
from unittest.mock import Mock, patch

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant
from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    client = APIClient()
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return client


def _make_invoice(tenant_id, country_code):
    Tenant.objects.create(
        id=tenant_id,
        name=f"Test Tenant {tenant_id}",
        slug=f"test-tenant-{tenant_id}",
        country_code=country_code,
    )
    control = Account.objects.create(tenant_id=tenant_id, code="1100", name="AR", account_type="asset")
    revenue = Account.objects.create(tenant_id=tenant_id, code="4000", name="Sales", account_type="income")
    tax = Account.objects.create(tenant_id=tenant_id, code="2200", name="Tax Payable", account_type="liability")
    partner = Partner.objects.create(tenant_id=tenant_id, name="Acme Co", partner_type="customer")
    invoice = Invoice.objects.create(
        tenant_id=tenant_id,
        invoice_type="customer",
        number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        partner=partner,
        date=date.today(),
        due_date=date.today(),
        control_account=control,
        tax_account=tax,
    )
    InvoiceLine.objects.create(
        tenant_id=tenant_id, invoice=invoice, account=revenue, quantity=1, unit_price=100, tax_percent=16,
    )
    return invoice


@pytest.mark.django_db
@pytest.mark.parametrize(
    "country_code,expected_region",
    [("JO", "JO"), ("SA", "SA"), ("AE", "AE"), ("US", "US")],
)
def test_post_invoice_routes_to_correct_compliance_region(
    admin_client, tenant_id, country_code, expected_region
):
    invoice = _make_invoice(tenant_id, country_code)

    with patch("products.cycom.ar_ap.compliance_client.httpx.post") as mock_post:
        mock_post.return_value = Mock(status_code=200, json=lambda: {"status": "ok"})
        mock_post.return_value.raise_for_status = lambda: None
        resp = admin_client.post(f"/api/v1/ar-ap/invoices/{invoice.id}/post/")

    assert resp.status_code == 200, resp.content
    assert resp.data["status"] == "posted"

    mock_post.assert_called_once()
    sent_url, sent_kwargs = mock_post.call_args
    assert sent_url[0].endswith("/api/compliance/process")
    assert sent_kwargs["json"]["region"] == expected_region
    assert sent_kwargs["json"]["invoice"]["amount_total"] == "116.00"


@pytest.mark.django_db
def test_post_invoice_unknown_country_skips_compliance_call_without_failing(admin_client, tenant_id):
    invoice = _make_invoice(tenant_id, "ZZ")  # not in the seeded catalog

    with patch("products.cycom.ar_ap.compliance_client.httpx.post") as mock_post:
        resp = admin_client.post(f"/api/v1/ar-ap/invoices/{invoice.id}/post/")

    assert resp.status_code == 200, resp.content
    assert resp.data["status"] == "posted"  # real GL posting still succeeds
    mock_post.assert_not_called()
