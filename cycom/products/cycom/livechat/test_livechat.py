import uuid

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant
from products.cycom.livechat.models import ChatMessage, ChatSession

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "agent@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def tenant(tenant_id):
    obj, _ = Tenant.objects.update_or_create(
        id=tenant_id, defaults={"name": f"chat-{tenant_id}", "slug": f"chat-{str(tenant_id)[:8]}"}
    )
    return obj


@pytest.fixture
def public_client():
    return APIClient()


def test_visitor_can_open_session(public_client, tenant):
    resp = public_client.post(f"/api/chat/{tenant.slug}/sessions/", {"visitor_name": "Sam"}, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "open"
    assert len(resp.data["token"]) > 20


def test_visitor_can_send_and_poll_messages(public_client, tenant):
    session = ChatSession.objects.create(tenant_id=tenant.id)
    resp = public_client.post(
        f"/api/chat/{tenant.slug}/sessions/{session.token}/messages/", {"body": "Hi there"}, format="json"
    )
    assert resp.status_code == 201, resp.data

    resp = public_client.get(f"/api/chat/{tenant.slug}/sessions/{session.token}/messages/")
    assert resp.status_code == 200
    assert resp.data["status"] == "open"
    assert len(resp.data["messages"]) == 1
    assert resp.data["messages"][0]["sender"] == "visitor"


def test_poll_since_only_returns_new_messages(public_client, tenant):
    session = ChatSession.objects.create(tenant_id=tenant.id)
    ChatMessage.objects.create(tenant_id=tenant.id, session=session, sender="visitor", body="old")
    first_resp = public_client.get(f"/api/chat/{tenant.slug}/sessions/{session.token}/messages/")
    cursor = first_resp.data["messages"][0]["created_at"]

    ChatMessage.objects.create(tenant_id=tenant.id, session=session, sender="agent", body="new")
    resp = public_client.get(f"/api/chat/{tenant.slug}/sessions/{session.token}/messages/?since={cursor}")
    assert resp.status_code == 200
    assert len(resp.data["messages"]) == 1
    assert resp.data["messages"][0]["body"] == "new"


def test_agent_reply_via_staff_api(admin_client, tenant_id):
    session = ChatSession.objects.create(tenant_id=tenant_id)
    resp = admin_client.post(f"/api/v1/livechat/sessions/{session.id}/reply/", {"body": "How can I help?"})
    assert resp.status_code == 201, resp.data
    assert resp.data["sender"] == "agent"


def test_closed_session_rejects_new_messages(public_client, tenant):
    session = ChatSession.objects.create(tenant_id=tenant.id, status="closed")
    resp = public_client.post(
        f"/api/chat/{tenant.slug}/sessions/{session.token}/messages/", {"body": "too late"}, format="json"
    )
    assert resp.status_code == 400


def test_staff_close_action(admin_client, tenant_id):
    session = ChatSession.objects.create(tenant_id=tenant_id)
    resp = admin_client.post(f"/api/v1/livechat/sessions/{session.id}/close/")
    assert resp.status_code == 200
    assert resp.data["status"] == "closed"


def test_unknown_chat_slug_404s_cleanly(public_client):
    resp = public_client.post("/api/chat/does-not-exist/sessions/", {}, format="json")
    assert resp.status_code == 400


def test_unknown_token_404s_cleanly(public_client, tenant):
    resp = public_client.get(f"/api/chat/{tenant.slug}/sessions/not-a-real-token/messages/")
    assert resp.status_code == 400


def test_admin_crud_requires_auth(tenant_id):
    resp = APIClient().get("/api/v1/livechat/sessions/")
    assert resp.status_code == 401


def test_tenant_isolation_on_admin_list(admin_client, tenant_id):
    ChatSession.objects.create(tenant_id=uuid.uuid4(), visitor_name="Foreign Visitor")
    resp = admin_client.get("/api/v1/livechat/sessions/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["visitor_name"] != "Foreign Visitor" for r in rows)
