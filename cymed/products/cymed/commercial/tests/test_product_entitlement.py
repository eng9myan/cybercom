"""
Standalone-products entitlement gating (Phase 1 of the "sell Hospital /
Clinic / Pharmacy / Laboratory / Imaging standalone" plan).

Covers EditionService.tenant_has_product() and ProductEntitlementMiddleware.
Middleware is tested directly against a stub get_response (not a full HTTP
round trip) so this doesn't depend on auth/view wiring for paths that may
not even resolve to a real view — the middleware blocks on request.path
alone, before Django's URL resolver ever runs.
"""
import uuid

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from products.cymed.commercial.editions.middleware import ProductEntitlementMiddleware
from products.cymed.commercial.editions.models import (
    ProductCatalogEntry,
    ProductEdition,
    TenantProductSubscription,
)
from products.cymed.commercial.editions.services import EditionService

PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def pharmacy_product(db):
    obj, _ = ProductCatalogEntry.objects.get_or_create(
        code="cymed_pharmacy",
        defaults={"tenant_id": PLATFORM_TENANT, "name": "CyMed Pharmacy", "is_active": True},
    )
    return obj


@pytest.fixture
def hospital_product(db):
    obj, _ = ProductCatalogEntry.objects.get_or_create(
        code="cymed_hospital",
        defaults={"tenant_id": PLATFORM_TENANT, "name": "CyMed Hospital", "is_active": True},
    )
    return obj


@pytest.fixture
def pharmacy_edition(db, pharmacy_product):
    obj, _ = ProductEdition.objects.get_or_create(
        product=pharmacy_product,
        code="retail",
        defaults={
            "tenant_id": PLATFORM_TENANT, "name": "Retail", "tier": "retail", "is_active": True,
        },
    )
    return obj


class TestTenantHasProduct:
    def test_unconfigured_tenant_has_full_legacy_access(self, db):
        tenant_id = uuid.uuid4()
        assert EditionService.tenant_has_product(tenant_id, "cymed_hospital") is True
        assert EditionService.tenant_has_product(tenant_id, "cymed_pharmacy") is True

    def test_pharmacy_only_tenant_is_blocked_from_other_products(
        self, db, pharmacy_product, pharmacy_edition
    ):
        tenant_id = uuid.uuid4()
        TenantProductSubscription.objects.create(
            tenant_id=tenant_id, product=pharmacy_product, edition=pharmacy_edition,
            is_active=True,
        )
        assert EditionService.tenant_has_product(tenant_id, "cymed_pharmacy") is True
        assert EditionService.tenant_has_product(tenant_id, "cymed_hospital") is False

    def test_churned_subscription_is_blocked_not_treated_as_legacy(
        self, db, pharmacy_product, pharmacy_edition
    ):
        tenant_id = uuid.uuid4()
        TenantProductSubscription.objects.create(
            tenant_id=tenant_id, product=pharmacy_product, edition=pharmacy_edition,
            is_active=False,
        )
        assert EditionService.tenant_has_product(tenant_id, "cymed_pharmacy") is False

    def test_tenant_entitled_products_lists_active_only(
        self, db, pharmacy_product, pharmacy_edition
    ):
        tenant_id = uuid.uuid4()
        TenantProductSubscription.objects.create(
            tenant_id=tenant_id, product=pharmacy_product, edition=pharmacy_edition,
            is_active=True,
        )
        assert EditionService.tenant_entitled_products(tenant_id) == ["cymed_pharmacy"]


class TestProductEntitlementMiddleware:
    def _request(self, path, tenant_id):
        req = RequestFactory().get(path)
        req.tenant_id = tenant_id
        return req

    def test_blocks_gated_path_for_unentitled_tenant(
        self, db, pharmacy_product, pharmacy_edition
    ):
        tenant_id = uuid.uuid4()
        TenantProductSubscription.objects.create(
            tenant_id=tenant_id, product=pharmacy_product, edition=pharmacy_edition,
            is_active=True,
        )
        downstream_called = []
        middleware = ProductEntitlementMiddleware(
            lambda r: downstream_called.append(True) or HttpResponse("ok")
        )
        resp = middleware(self._request("/api/v1/hospital/encounters/", tenant_id))
        assert resp.status_code == 403
        assert resp["Content-Type"] == "application/problem+json"
        assert downstream_called == []

    def test_allows_gated_path_for_entitled_tenant(self, db, pharmacy_product, pharmacy_edition):
        tenant_id = uuid.uuid4()
        TenantProductSubscription.objects.create(
            tenant_id=tenant_id, product=pharmacy_product, edition=pharmacy_edition,
            is_active=True,
        )
        middleware = ProductEntitlementMiddleware(lambda r: HttpResponse("ok"))
        resp = middleware(self._request("/api/v1/pharmacy/dispensing/", tenant_id))
        assert resp.status_code == 200

    def test_allows_legacy_tenant_through_every_gated_path(self, db):
        tenant_id = uuid.uuid4()
        middleware = ProductEntitlementMiddleware(lambda r: HttpResponse("ok"))
        for path in (
            "/api/v1/hospital/x/", "/api/v1/clinic/x/", "/api/v1/lab/x/",
            "/api/v1/imaging/x/", "/api/v1/pharmacy/x/",
        ):
            assert middleware(self._request(path, tenant_id)).status_code == 200

    def test_ungated_path_always_passes_through(self, db, pharmacy_product, pharmacy_edition):
        tenant_id = uuid.uuid4()
        TenantProductSubscription.objects.create(
            tenant_id=tenant_id, product=pharmacy_product, edition=pharmacy_edition,
            is_active=True,
        )
        middleware = ProductEntitlementMiddleware(lambda r: HttpResponse("ok"))
        resp = middleware(self._request("/api/v1/patients/", tenant_id))
        assert resp.status_code == 200

    def test_missing_tenant_id_passes_through(self, db):
        middleware = ProductEntitlementMiddleware(lambda r: HttpResponse("ok"))
        req = RequestFactory().get("/api/v1/hospital/x/")
        assert middleware(req).status_code == 200
