import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.discuss.models import Channel


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
def test_channel_message_flow(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/discuss/channels/",
        {"name": "general", "channel_type": "channel"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    channel_id = resp.data["id"]

    resp = platform_admin_client.post(
        "/api/v1/discuss/messages/",
        {"channel": channel_id, "author": "Ahmad", "body": "Hello team"},
        format="json",
    )
    assert resp.status_code == 201, resp.data

    resp = platform_admin_client.get(f"/api/v1/discuss/messages/?channel={channel_id}")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert rows[0]["body"] == "Hello team"


@pytest.mark.django_db
def test_channel_tenant_isolation(platform_admin_client, tenant_id):
    Channel.objects.create(tenant_id=uuid.uuid4(), name="foreign-channel")
    resp = platform_admin_client.get("/api/v1/discuss/channels/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "foreign-channel" for r in rows)
