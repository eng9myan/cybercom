import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.marketing.models import Campaign


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
    return client


@pytest.mark.django_db
def test_create_and_list_campaign(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/marketing/campaigns/",
        {"name": "Summer Sale", "campaign_type": "email", "target": "All Customers"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["state"] == "draft"

    resp = platform_admin_client.get("/api/v1/marketing/campaigns/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert any(r["name"] == "Summer Sale" for r in rows)


@pytest.mark.django_db
def test_campaign_tenant_isolation(platform_admin_client, tenant_id):
    Campaign.objects.create(tenant_id=uuid.uuid4(), name="Foreign Campaign")
    resp = platform_admin_client.get("/api/v1/marketing/campaigns/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign Campaign" for r in rows)
