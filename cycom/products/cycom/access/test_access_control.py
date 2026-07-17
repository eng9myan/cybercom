import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.access.models import AccessGrant, Role, RoleAssignment
from products.cycom.inventory.models import Product, Warehouse


def _client(mint_token, mock_jwks, tenant_id, user_id, roles=None):
    token = mint_token(
        {
            "sub": user_id,
            "email": f"{user_id}@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": roles or []},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def inventory_fixtures(db, tenant_id):
    inventory_account = Account.objects.create(
        tenant_id=tenant_id, code="1200", name="Inventory", account_type="asset"
    )
    wh_main = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main")
    wh_branch = Warehouse.objects.create(tenant_id=tenant_id, code="WH-BR1", name="Branch 1")
    prod_a = Product.objects.create(
        tenant_id=tenant_id, sku="A", name="Widget A", inventory_account=inventory_account
    )
    prod_b = Product.objects.create(
        tenant_id=tenant_id, sku="B", name="Widget B", inventory_account=inventory_account
    )
    return {"wh_main": wh_main, "wh_branch": wh_branch, "prod_a": prod_a, "prod_b": prod_b}


@pytest.mark.django_db
def test_user_with_no_grants_sees_everything(mint_token, mock_jwks, tenant_id, inventory_fixtures):
    client = _client(mint_token, mock_jwks, tenant_id, "user-unrestricted")

    resp = client.get("/api/v1/inventory/warehouses/")
    assert resp.status_code == 200
    assert resp.data["count"] == 2

    resp = client.get("/api/v1/inventory/products/")
    assert resp.status_code == 200
    assert resp.data["count"] == 2


@pytest.mark.django_db
def test_direct_user_grant_restricts_warehouse_visibility(
    mint_token, mock_jwks, tenant_id, inventory_fixtures
):
    user_id = "user-restricted"
    AccessGrant.objects.create(
        tenant_id=tenant_id,
        subject_type="user",
        user_id=user_id,
        warehouse=inventory_fixtures["wh_branch"],
    )
    client = _client(mint_token, mock_jwks, tenant_id, user_id)

    resp = client.get("/api/v1/inventory/warehouses/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["id"] == str(inventory_fixtures["wh_branch"].id)

    # Product dimension untouched by a warehouse-only grant — still unrestricted.
    resp = client.get("/api/v1/inventory/products/")
    assert resp.status_code == 200
    assert resp.data["count"] == 2


@pytest.mark.django_db
def test_role_based_grant_restricts_product_visibility(
    mint_token, mock_jwks, tenant_id, inventory_fixtures
):
    role = Role.objects.create(tenant_id=tenant_id, name="Branch Staff")
    AccessGrant.objects.create(
        tenant_id=tenant_id, subject_type="role", role=role, product=inventory_fixtures["prod_a"]
    )
    user_id = "user-with-role"
    RoleAssignment.objects.create(tenant_id=tenant_id, user_id=user_id, role=role)

    client = _client(mint_token, mock_jwks, tenant_id, user_id)

    resp = client.get("/api/v1/inventory/products/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["sku"] == "A"

    # A different user not assigned the role is unaffected.
    other_client = _client(mint_token, mock_jwks, tenant_id, "user-no-role")
    resp = other_client.get("/api/v1/inventory/products/")
    assert resp.status_code == 200
    assert resp.data["count"] == 2


@pytest.mark.django_db
def test_platform_admin_bypasses_restrictions(mint_token, mock_jwks, tenant_id, inventory_fixtures):
    AccessGrant.objects.create(
        tenant_id=tenant_id,
        subject_type="user",
        user_id="admin-1",
        warehouse=inventory_fixtures["wh_branch"],
    )
    client = _client(mint_token, mock_jwks, tenant_id, "admin-1", roles=["platform_admin"])

    resp = client.get("/api/v1/inventory/warehouses/")
    assert resp.status_code == 200
    assert resp.data["count"] == 2


@pytest.mark.django_db
def test_non_admin_cannot_manage_grants(mint_token, mock_jwks, tenant_id, inventory_fixtures):
    client = _client(mint_token, mock_jwks, tenant_id, "regular-user")
    resp = client.post(
        "/api/v1/access/grants/",
        {"subject_type": "user", "user_id": "someone", "warehouse": str(inventory_fixtures["wh_main"].id)},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_platform_admin_can_create_grant_via_api(mint_token, mock_jwks, tenant_id, inventory_fixtures):
    client = _client(mint_token, mock_jwks, tenant_id, "admin-2", roles=["platform_admin"])
    resp = client.post(
        "/api/v1/access/grants/",
        {"subject_type": "user", "user_id": "cashier-9", "warehouse": str(inventory_fixtures["wh_main"].id)},
        format="json",
    )
    assert resp.status_code == 201
    assert AccessGrant.objects.filter(tenant_id=tenant_id, user_id="cashier-9").exists()


@pytest.mark.django_db
def test_grant_requires_warehouse_or_product(mint_token, mock_jwks, tenant_id, inventory_fixtures):
    client = _client(mint_token, mock_jwks, tenant_id, "admin-3", roles=["platform_admin"])
    resp = client.post(
        "/api/v1/access/grants/", {"subject_type": "user", "user_id": "x"}, format="json"
    )
    assert resp.status_code == 400
