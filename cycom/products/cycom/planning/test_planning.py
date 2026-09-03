import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.planning.models import ShiftSlot


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
def test_create_and_list_slot(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/planning/slots/",
        {
            "resource_name": "Ahmad",
            "role": "Cashier",
            "department": "sales",
            "start_datetime": "2026-08-10T09:00:00Z",
            "end_datetime": "2026-08-10T17:00:00Z",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data

    resp = platform_admin_client.get("/api/v1/planning/slots/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert any(r["resource_name"] == "Ahmad" for r in rows)


@pytest.mark.django_db
def test_slot_tenant_isolation(platform_admin_client, tenant_id):
    ShiftSlot.objects.create(tenant_id=uuid.uuid4(), resource_name="Foreign")
    resp = platform_admin_client.get("/api/v1/planning/slots/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["resource_name"] != "Foreign" for r in rows)
