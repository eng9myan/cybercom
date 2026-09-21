import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.company.models import Company


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
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
    return client


@pytest.mark.django_db
def test_create_company(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/company/companies/",
        {"name": "Acme Jordan", "legal_name": "Acme Jordan LLC", "tax_id": "JO-123", "currency": "JOD"},
        format="json",
    )
    assert resp.status_code == 201, resp.data


@pytest.mark.django_db
def test_subsidiary_relationship(admin_client, tenant_id):
    parent = Company.objects.create(tenant_id=tenant_id, name="Acme Holding")
    resp = admin_client.post(
        "/api/v1/company/companies/",
        {"name": "Acme Jordan", "parent_company": str(parent.id)},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert str(resp.data["parent_company"]) == str(parent.id)


@pytest.mark.django_db
def test_tenant_isolation(admin_client):
    Company.objects.create(tenant_id=uuid.uuid4(), name="Foreign Co")
    resp = admin_client.get("/api/v1/company/companies/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign Co" for r in rows)
