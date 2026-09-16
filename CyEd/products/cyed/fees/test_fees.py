import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import Student


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_invoice_partial_then_full_payment(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)

    inv = platform_admin_client.post(
        "/api/v1/fees/invoices/",
        {"student": str(student.id), "description": "Term 1 Tuition", "amount": "1000.00",
         "status": "issued", "issued_on": "2026-02-01"},
        format="json",
    )
    assert inv.status_code == 201, inv.data
    invoice_id = inv.data["id"]
    assert inv.data["balance"] == "1000.00"

    # Partial payment.
    p1 = platform_admin_client.post(
        "/api/v1/fees/payments/",
        {"invoice": invoice_id, "amount": "400.00", "method": "bpay"},
        format="json",
    )
    assert p1.status_code == 201, p1.data

    detail = platform_admin_client.get(f"/api/v1/fees/invoices/{invoice_id}/")
    assert detail.data["paid_total"] == "400.00"
    assert detail.data["balance"] == "600.00"
    assert detail.data["status"] == "partial"

    # Remaining payment settles the invoice.
    platform_admin_client.post(
        "/api/v1/fees/payments/",
        {"invoice": invoice_id, "amount": "600.00", "method": "card"},
        format="json",
    )
    settled = platform_admin_client.get(f"/api/v1/fees/invoices/{invoice_id}/")
    assert settled.data["balance"] == "0.00"
    assert settled.data["status"] == "paid"


@pytest.mark.django_db
def test_invoice_tenant_isolation(platform_admin_client, tenant_id):
    other = uuid.uuid4()
    s = Student.objects.create(tenant_id=other, first_name="Foreign", last_name="Kid", year_level=8)
    from products.cyed.fees.models import Invoice
    Invoice.objects.create(tenant_id=other, student=s, amount="500", description="Foreign fee")
    resp = platform_admin_client.get("/api/v1/fees/invoices/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["description"] != "Foreign fee" for r in rows)
