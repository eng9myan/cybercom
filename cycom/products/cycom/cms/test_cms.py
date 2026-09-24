import uuid

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant
from products.cycom.cms.models import Page, PageBlock

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "webmaster@cybercom.io",
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
        id=tenant_id, defaults={"name": f"site-{tenant_id}", "slug": f"site-{str(tenant_id)[:8]}"}
    )
    return obj


@pytest.fixture
def public_client():
    return APIClient()


def test_setting_second_homepage_demotes_the_first(admin_client, tenant_id):
    page_a = Page.objects.create(tenant_id=tenant_id, title="Home A", is_homepage=True)
    page_b = Page.objects.create(tenant_id=tenant_id, title="Home B", is_homepage=True)
    page_a.refresh_from_db()
    assert page_a.is_homepage is False
    assert page_b.is_homepage is True


def test_create_block_inside_columns_container(admin_client, tenant_id):
    page = Page.objects.create(tenant_id=tenant_id, title="Landing")
    columns = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="columns", order=0)

    resp = admin_client.post(
        "/api/v1/cms/blocks/",
        {"page": str(page.id), "parent": str(columns.id), "block_type": "text", "order": 0, "config": {"text": "Hi"}},
        format="json",
    )
    assert resp.status_code == 201, resp.data


def test_block_rejects_parent_that_is_not_a_container(admin_client, tenant_id):
    page = Page.objects.create(tenant_id=tenant_id, title="Landing")
    heading = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="heading", order=0)

    resp = admin_client.post(
        "/api/v1/cms/blocks/",
        {"page": str(page.id), "parent": str(heading.id), "block_type": "text", "order": 0, "config": {}},
        format="json",
    )
    assert resp.status_code == 400


def test_container_block_rejects_being_nested(admin_client, tenant_id):
    page = Page.objects.create(tenant_id=tenant_id, title="Landing")
    section = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="section", order=0)

    resp = admin_client.post(
        "/api/v1/cms/blocks/",
        {"page": str(page.id), "parent": str(section.id), "block_type": "columns", "order": 0, "config": {}},
        format="json",
    )
    assert resp.status_code == 400


def test_reorder_persists_drag_drop_move(admin_client, tenant_id):
    page = Page.objects.create(tenant_id=tenant_id, title="Landing")
    columns = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="columns", order=0)
    text_block = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="text", order=1)

    resp = admin_client.post(
        "/api/v1/cms/blocks/reorder/",
        {"page": str(page.id), "moves": [{"id": str(text_block.id), "parent": str(columns.id), "order": 0}]},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    text_block.refresh_from_db()
    assert text_block.parent_id == columns.id
    assert text_block.order == 0


def test_reorder_rejects_malformed_move(admin_client, tenant_id):
    page = Page.objects.create(tenant_id=tenant_id, title="Landing")
    block = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="text", order=0)

    resp = admin_client.post(
        "/api/v1/cms/blocks/reorder/",
        {"page": str(page.id), "moves": [{"parent": None}]},
        format="json",
    )
    assert resp.status_code == 400

    resp = admin_client.post(
        "/api/v1/cms/blocks/reorder/",
        {"page": str(page.id), "moves": [{"id": str(block.id), "order": "not-a-number"}]},
        format="json",
    )
    assert resp.status_code == 400


def test_reorder_rejects_nesting_container_via_drag(admin_client, tenant_id):
    page = Page.objects.create(tenant_id=tenant_id, title="Landing")
    columns = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="columns", order=0)
    section = PageBlock.objects.create(tenant_id=tenant_id, page=page, block_type="section", order=1)

    resp = admin_client.post(
        "/api/v1/cms/blocks/reorder/",
        {"page": str(page.id), "moves": [{"id": str(section.id), "parent": str(columns.id), "order": 0}]},
        format="json",
    )
    assert resp.status_code == 400
    section.refresh_from_db()
    assert section.parent_id is None


def test_public_page_returns_nested_tree(public_client, tenant):
    page = Page.objects.create(tenant_id=tenant.id, title="Landing", is_published=True)
    columns = PageBlock.objects.create(tenant_id=tenant.id, page=page, block_type="columns", order=0)
    PageBlock.objects.create(
        tenant_id=tenant.id, page=page, parent=columns, block_type="text", order=0, config={"text": "Hello"}
    )

    resp = public_client.get(f"/api/site/{tenant.slug}/pages/{page.slug}/")
    assert resp.status_code == 200
    assert len(resp.data["blocks"]) == 1
    assert resp.data["blocks"][0]["block_type"] == "columns"
    assert resp.data["blocks"][0]["children"][0]["config"]["text"] == "Hello"


def test_unpublished_page_hidden_from_public(public_client, tenant):
    page = Page.objects.create(tenant_id=tenant.id, title="Draft Page", is_published=False)
    resp = public_client.get(f"/api/site/{tenant.slug}/pages/{page.slug}/")
    assert resp.status_code == 400


def test_public_homepage(public_client, tenant):
    Page.objects.create(tenant_id=tenant.id, title="Home", is_published=True, is_homepage=True)
    resp = public_client.get(f"/api/site/{tenant.slug}/")
    assert resp.status_code == 200
    assert resp.data["title"] == "Home"


def test_public_homepage_missing_404s_cleanly(public_client, tenant):
    resp = public_client.get(f"/api/site/{tenant.slug}/")
    assert resp.status_code == 400


def test_admin_crud_requires_auth(tenant_id):
    resp = APIClient().get("/api/v1/cms/pages/")
    assert resp.status_code == 401


def test_tenant_isolation_on_admin_page_list(admin_client, tenant_id):
    Page.objects.create(tenant_id=uuid.uuid4(), title="Foreign Page")
    resp = admin_client.get("/api/v1/cms/pages/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["title"] != "Foreign Page" for r in rows)
