import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cymart.merchants.models import Merchant, Product
from products.cymart.merchants.services import CatalogSearch


def _authed_client(mint_token, mock_jwks, user_id):
    client = APIClient()
    token = mint_token({"sub": str(user_id), "roles": ["customer"], "permissions": []})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestCatalogSearch:
    def test_seed_migration_created_25_restaurants_and_3_hypermarkets(self):
        assert Merchant.objects.filter(kind="restaurant").count() == 25
        assert Merchant.objects.filter(kind="hypermarket").count() == 3

    def test_safeway_duplicates_hypermax_catalog(self):
        hypermax = Merchant.objects.get(name="HyperMax")
        safeway = Merchant.objects.get(name="Safeway")
        assert hypermax.products.count() == safeway.products.count()
        hypermax_names = set(hypermax.products.values_list("name", flat=True))
        safeway_names = set(safeway.products.values_list("name", flat=True))
        assert hypermax_names == safeway_names

    def test_search_finds_real_seeded_item(self):
        results = CatalogSearch().search("shawarma")
        assert len(results) > 0
        assert any("shawarma" in r["name"].lower() for r in results)

    def test_search_by_kind_only_returns_hypermarkets(self):
        results = CatalogSearch().search("", kind="hypermarket", limit=50)
        assert all(r["merchant_kind"] == "hypermarket" for r in results)

    def test_every_seeded_product_has_store_and_tenant_id(self):
        results = CatalogSearch().search("chicken", limit=5)
        for r in results:
            assert r["store_id"] is not None
            assert r["tenant_id"] is not None
            assert r["price"] > 0


@pytest.mark.django_db
class TestMerchantAPI:
    def test_list_requires_auth(self):
        resp = APIClient().get("/api/v1/merchants/")
        assert resp.status_code in (401, 403)

    def test_list_restaurants_only(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.get("/api/v1/merchants/?kind=restaurant")
        assert resp.status_code == 200
        assert len(resp.json()) == 25

    def test_merchant_detail_includes_products(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        merchant = Merchant.objects.filter(kind="restaurant").first()
        resp = client.get(f"/api/v1/merchants/{merchant.id}/")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["products"]) == 4

    def test_search_endpoint(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.get("/api/v1/merchants/search/?q=mansaf")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
