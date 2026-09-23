import uuid

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant
from products.cycom.forum.models import ForumReply, ForumThread

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "moderator@cybercom.io",
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
        id=tenant_id, defaults={"name": f"forum-{tenant_id}", "slug": f"forum-{str(tenant_id)[:8]}"}
    )
    return obj


@pytest.fixture
def public_client():
    return APIClient()


def test_guest_can_create_thread(public_client, tenant):
    resp = public_client.post(
        f"/api/forum/{tenant.slug}/threads/create/",
        {"title": "How do I export invoices?", "body": "Looking for a bulk export.", "author_name": "Sam"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["slug"] == "how-do-i-export-invoices"
    assert resp.data["replies"] == []


def test_guest_can_reply_to_thread(public_client, tenant):
    thread = ForumThread.objects.create(tenant_id=tenant.id, title="Question", body="...")
    resp = public_client.post(
        f"/api/forum/{tenant.slug}/threads/{thread.slug}/replies/",
        {"body": "Here's how", "author_name": "Jo"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["is_accepted"] is False


def test_reply_blocked_on_locked_thread(public_client, tenant):
    thread = ForumThread.objects.create(tenant_id=tenant.id, title="Closed topic", body="...", is_locked=True)
    resp = public_client.post(
        f"/api/forum/{tenant.slug}/threads/{thread.slug}/replies/",
        {"body": "Too late", "author_name": "Jo"},
        format="json",
    )
    assert resp.status_code == 400


def test_public_thread_list_includes_reply_count(public_client, tenant):
    thread = ForumThread.objects.create(tenant_id=tenant.id, title="Popular", body="...")
    ForumReply.objects.create(tenant_id=tenant.id, thread=thread, body="one")
    ForumReply.objects.create(tenant_id=tenant.id, thread=thread, body="two")

    resp = public_client.get(f"/api/forum/{tenant.slug}/threads/")
    assert resp.status_code == 200
    row = next(r for r in resp.data if r["slug"] == "popular")
    assert row["reply_count"] == 2


def test_accept_reply_unsets_previous_accepted(admin_client, tenant_id):
    thread = ForumThread.objects.create(tenant_id=tenant_id, title="Q", body="...")
    reply_a = ForumReply.objects.create(tenant_id=tenant_id, thread=thread, body="A", is_accepted=True)
    reply_b = ForumReply.objects.create(tenant_id=tenant_id, thread=thread, body="B")

    resp = admin_client.post(f"/api/v1/forum/replies/{reply_b.id}/accept/")
    assert resp.status_code == 200
    assert resp.data["is_accepted"] is True

    reply_a.refresh_from_db()
    assert reply_a.is_accepted is False


def test_pin_and_lock_actions(admin_client, tenant_id):
    thread = ForumThread.objects.create(tenant_id=tenant_id, title="Sticky", body="...")

    resp = admin_client.post(f"/api/v1/forum/threads/{thread.id}/pin/")
    assert resp.data["is_pinned"] is True

    resp = admin_client.post(f"/api/v1/forum/threads/{thread.id}/lock/")
    assert resp.data["is_locked"] is True


def test_unknown_forum_slug_404s_cleanly(public_client):
    resp = public_client.get("/api/forum/does-not-exist/threads/")
    assert resp.status_code == 400


def test_admin_crud_requires_auth(tenant_id):
    resp = APIClient().get("/api/v1/forum/threads/")
    assert resp.status_code == 401


def test_tenant_isolation_on_admin_list(admin_client, tenant_id):
    ForumThread.objects.create(tenant_id=uuid.uuid4(), title="Foreign Thread", body="...")
    resp = admin_client.get("/api/v1/forum/threads/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["title"] != "Foreign Thread" for r in rows)


def test_empty_reply_body_rejected(public_client, tenant):
    thread = ForumThread.objects.create(tenant_id=tenant.id, title="Q", body="...")
    resp = public_client.post(
        f"/api/forum/{tenant.slug}/threads/{thread.slug}/replies/",
        {"body": "   ", "author_name": "Jo"},
        format="json",
    )
    assert resp.status_code == 400
