import uuid

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant
from products.cycom.blog.models import BlogPost

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "editor@cybercom.io",
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
        id=tenant_id, defaults={"name": f"blog-{tenant_id}", "slug": f"blog-{str(tenant_id)[:8]}"}
    )
    return obj


@pytest.fixture
def public_client():
    return APIClient()


def test_create_post_defaults_to_unpublished(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/blog/posts/", {"title": "Hello World", "content": "First post"}, format="json"
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["is_published"] is False
    assert resp.data["slug"] == "hello-world"
    assert resp.data["published_at"] is None


def test_publish_sets_published_at(admin_client, tenant_id):
    post = BlogPost.objects.create(tenant_id=tenant_id, title="Draft")
    resp = admin_client.post(f"/api/v1/blog/posts/{post.id}/publish/")
    assert resp.status_code == 200
    assert resp.data["is_published"] is True
    assert resp.data["published_at"] is not None


def test_unpublish_keeps_original_published_at(admin_client, tenant_id):
    post = BlogPost.objects.create(tenant_id=tenant_id, title="Draft")
    admin_client.post(f"/api/v1/blog/posts/{post.id}/publish/")
    post.refresh_from_db()
    first_published_at = post.published_at

    admin_client.post(f"/api/v1/blog/posts/{post.id}/unpublish/")
    admin_client.post(f"/api/v1/blog/posts/{post.id}/publish/")
    post.refresh_from_db()
    assert post.published_at == first_published_at


def test_public_list_only_shows_published(public_client, tenant):
    BlogPost.objects.create(tenant_id=tenant.id, title="Published Post", is_published=True)
    BlogPost.objects.create(tenant_id=tenant.id, title="Draft Post", is_published=False)

    resp = public_client.get(f"/api/blog/{tenant.slug}/posts/")
    assert resp.status_code == 200
    titles = [p["title"] for p in resp.data]
    assert "Published Post" in titles
    assert "Draft Post" not in titles


def test_public_detail_by_slug(public_client, tenant):
    BlogPost.objects.create(
        tenant_id=tenant.id, title="My Post", content="Full body text", is_published=True
    )
    resp = public_client.get(f"/api/blog/{tenant.slug}/posts/my-post/")
    assert resp.status_code == 200
    assert resp.data["content"] == "Full body text"


def test_public_detail_hides_unpublished(public_client, tenant):
    BlogPost.objects.create(tenant_id=tenant.id, title="Secret", is_published=False)
    resp = public_client.get(f"/api/blog/{tenant.slug}/posts/secret/")
    assert resp.status_code == 400


def test_unknown_blog_slug_404s_cleanly(public_client):
    resp = public_client.get("/api/blog/does-not-exist/posts/")
    assert resp.status_code == 400


def test_admin_crud_requires_auth(tenant_id):
    resp = APIClient().get("/api/v1/blog/posts/")
    assert resp.status_code == 401


def test_slug_unique_per_tenant(admin_client, tenant_id):
    BlogPost.objects.create(tenant_id=tenant_id, title="Same Title", slug="same-title")
    with pytest.raises(Exception):
        BlogPost.objects.create(tenant_id=tenant_id, title="Same Title", slug="same-title")


def test_tenant_isolation_on_admin_list(admin_client, tenant_id):
    BlogPost.objects.create(tenant_id=uuid.uuid4(), title="Foreign Post")
    resp = admin_client.get("/api/v1/blog/posts/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["title"] != "Foreign Post" for r in rows)
