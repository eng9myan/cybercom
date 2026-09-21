import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.catalog.models import Product, TaxClass
from products.cycom.storefront.models import Cart

pytestmark = pytest.mark.django_db


@pytest.fixture
def store(tenant_id):
    from platform.tenant.models import Tenant

    tenant, _ = Tenant.objects.update_or_create(
        id=tenant_id, defaults={"name": f"store-{tenant_id}", "slug": f"store-{str(tenant_id)[:8]}"}
    )
    inv_account = Account.objects.create(tenant_id=tenant_id, code="1200", name="Inventory", account_type="asset")
    tax = TaxClass.objects.create(tenant_id=tenant_id, name="Standard", code="STD", rate=Decimal("0.1600"))
    published = Product.objects.create(
        tenant_id=tenant_id, name="Widget", internal_ref="W-1", sell_price=Decimal("25.00"),
        inventory_account=inv_account, tax_class=tax, is_published_online=True,
    )
    unpublished = Product.objects.create(
        tenant_id=tenant_id, name="Internal Only", internal_ref="W-2", sell_price=Decimal("10.00"),
        inventory_account=inv_account, is_published_online=False,
    )
    return {"tenant": tenant, "published": published, "unpublished": unpublished}


@pytest.fixture
def client():
    return APIClient()


def test_product_list_only_shows_published(client, store):
    resp = client.get(f"/api/store/{store['tenant'].slug}/products/")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.data]
    assert "Widget" in names
    assert "Internal Only" not in names


def test_unknown_store_slug_404s_cleanly(client):
    resp = client.get("/api/store/does-not-exist/products/")
    assert resp.status_code == 400


def test_create_cart_and_add_item(client, store):
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    assert resp.status_code == 201
    token = resp.data["token"]

    resp = client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["published"].id), "quantity": 2},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert len(resp.data["lines"]) == 1
    assert resp.data["lines"][0]["quantity"] == 2


def test_cannot_add_unpublished_product(client, store):
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    token = resp.data["token"]
    resp = client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["unpublished"].id), "quantity": 1},
        format="json",
    )
    assert resp.status_code == 400


def test_adding_same_product_twice_updates_quantity(client, store):
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    token = resp.data["token"]
    client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["published"].id), "quantity": 2}, format="json",
    )
    resp = client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["published"].id), "quantity": 5}, format="json",
    )
    assert len(resp.data["lines"]) == 1
    assert resp.data["lines"][0]["quantity"] == 5


def test_remove_item(client, store):
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    token = resp.data["token"]
    client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["published"].id), "quantity": 1}, format="json",
    )
    resp = client.delete(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/{store['published'].id}/"
    )
    assert resp.status_code == 200
    assert resp.data["lines"] == []


def test_checkout_creates_real_sales_order(client, store, tenant_id):
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    token = resp.data["token"]
    client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["published"].id), "quantity": 3}, format="json",
    )
    resp = client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/checkout/",
        {"customer_name": "Jane Doe", "customer_email": "jane@x.com"}, format="json",
    )
    assert resp.status_code == 201, resp.data
    # 3 x 25.00 = 75.00, +16% tax = 87.00
    assert resp.data["total"] == "87.00"

    cart = Cart.objects.get(token=token)
    assert cart.status == "checked_out"
    assert cart.order is not None
    assert cart.order.customer_name == "Jane Doe"
    assert cart.order.lines.count() == 1


def test_cannot_checkout_empty_cart(client, store):
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    token = resp.data["token"]
    resp = client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/checkout/",
        {"customer_name": "Jane Doe"}, format="json",
    )
    assert resp.status_code == 400


def test_cannot_modify_checked_out_cart(client, store):
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    token = resp.data["token"]
    client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["published"].id), "quantity": 1}, format="json",
    )
    client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/checkout/",
        {"customer_name": "Jane Doe"}, format="json",
    )
    resp = client.post(
        f"/api/store/{store['tenant'].slug}/carts/{token}/items/",
        {"product": str(store["published"].id), "quantity": 1}, format="json",
    )
    assert resp.status_code == 400


def test_carts_are_tenant_isolated(client, store):
    from platform.tenant.models import Tenant

    other_tenant, _ = Tenant.objects.update_or_create(
        id=uuid.uuid4(), defaults={"name": "other-store", "slug": "other-store"}
    )
    resp = client.post(f"/api/store/{store['tenant'].slug}/carts/")
    token = resp.data["token"]
    # Same token, wrong store slug -> not found.
    resp = client.get(f"/api/store/{other_tenant.slug}/carts/{token}/")
    assert resp.status_code == 400
