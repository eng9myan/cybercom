import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.plm.models import EngineeringChangeOrder, ProductBOM


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
def test_create_eco_and_bom_with_components(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/plm/ecos/",
        {"name": "ECO-100", "product_name": "Olive Oil Carton", "stage": "review"},
        format="json",
    )
    assert resp.status_code == 201, resp.data

    bom = ProductBOM.objects.create(tenant_id=tenant_id, product_name="Carton", sku="X")
    resp = platform_admin_client.post(
        "/api/v1/plm/bom-components/",
        {"bom": str(bom.id), "name": "Glass Bottle", "qty_needed": "6", "unit_cost": "0.35"},
        format="json",
    )
    assert resp.status_code == 201, resp.data

    resp = platform_admin_client.get(f"/api/v1/plm/boms/{bom.id}/")
    assert resp.status_code == 200
    assert len(resp.data["components"]) == 1


@pytest.mark.django_db
def test_eco_tenant_isolation(platform_admin_client, tenant_id):
    EngineeringChangeOrder.objects.create(tenant_id=uuid.uuid4(), name="Foreign ECO")
    resp = platform_admin_client.get("/api/v1/plm/ecos/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign ECO" for r in rows)
