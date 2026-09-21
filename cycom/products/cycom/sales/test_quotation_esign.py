"""Quotation templates + e-sign-on-quote (Phase 1 Odoo gap-closure)."""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cycom.esign.models import SignTemplate
from products.cycom.sales.models import QuotationTemplate, QuotationTemplateLine, SalesOrder


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "sales@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def order(db, tenant_id):
    return SalesOrder.objects.create(
        tenant_id=tenant_id, number="Q-100", customer_name="Acme Corp", order_date=date.today()
    )


@pytest.mark.django_db
def test_apply_template_replaces_lines(admin_client, tenant_id, order):
    template = QuotationTemplate.objects.create(
        tenant_id=tenant_id, name="Standard Package", terms="Net 30", validity_days=15
    )
    QuotationTemplateLine.objects.create(
        tenant_id=tenant_id, template=template, description="Setup fee", quantity=1, unit_price=100
    )
    QuotationTemplateLine.objects.create(
        tenant_id=tenant_id, template=template, description="Monthly fee", quantity=12, unit_price=50
    )

    resp = admin_client.post(
        f"/api/v1/sales/orders/{order.id}/apply-template/", {"template_id": str(template.id)}, format="json"
    )
    assert resp.status_code == 200, resp.data
    assert len(resp.data["lines"]) == 2
    assert resp.data["terms"] == "Net 30"
    assert resp.data["valid_until"] is not None
    assert resp.data["amount_subtotal"] != "0.00"


@pytest.mark.django_db
def test_apply_template_rejected_once_confirmed(admin_client, tenant_id, order):
    from products.cycom.sales.models import SalesOrderLine

    SalesOrderLine.objects.create(tenant_id=tenant_id, order=order, quantity=1, unit_price=10)
    order.status = "confirmed"
    order.save(update_fields=["status"])
    template = QuotationTemplate.objects.create(tenant_id=tenant_id, name="X", validity_days=1)

    resp = admin_client.post(
        f"/api/v1/sales/orders/{order.id}/apply-template/", {"template_id": str(template.id)}, format="json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_request_signature_links_sign_request(admin_client, tenant_id, order):
    sign_template = SignTemplate.objects.create(
        tenant_id=tenant_id, name="Quote Terms", file="cycom_esign/templates/terms.pdf"
    )
    resp = admin_client.post(
        f"/api/v1/sales/orders/{order.id}/request-signature/",
        {"sign_template_id": str(sign_template.id), "signer_email": "buyer@acme.com"},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["sign_status"] == "Sent"
    order.refresh_from_db()
    assert order.sign_request is not None
    assert order.sign_request.signers == [{"name": "Acme Corp", "email": "buyer@acme.com"}]


@pytest.mark.django_db
def test_confirm_blocked_until_signed(admin_client, tenant_id, order):
    from products.cycom.sales.models import SalesOrderLine

    SalesOrderLine.objects.create(tenant_id=tenant_id, order=order, quantity=1, unit_price=10)
    sign_template = SignTemplate.objects.create(
        tenant_id=tenant_id, name="Quote Terms", file="cycom_esign/templates/terms.pdf"
    )
    admin_client.post(
        f"/api/v1/sales/orders/{order.id}/request-signature/",
        {"sign_template_id": str(sign_template.id)},
        format="json",
    )

    resp = admin_client.post(f"/api/v1/sales/orders/{order.id}/confirm/")
    assert resp.status_code == 400

    order.refresh_from_db()
    order.sign_request.status = "Signed"
    order.sign_request.save(update_fields=["status"])

    resp = admin_client.post(f"/api/v1/sales/orders/{order.id}/confirm/")
    assert resp.status_code == 200
    assert resp.data["status"] == "confirmed"


@pytest.mark.django_db
def test_confirm_unaffected_when_no_signature_requested(admin_client, tenant_id, order):
    from products.cycom.sales.models import SalesOrderLine

    SalesOrderLine.objects.create(tenant_id=tenant_id, order=order, quantity=1, unit_price=10)
    resp = admin_client.post(f"/api/v1/sales/orders/{order.id}/confirm/")
    assert resp.status_code == 200
