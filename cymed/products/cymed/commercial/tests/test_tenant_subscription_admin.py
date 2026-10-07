"""
Admin provisioning UI backend: TenantProductSubscriptionViewSet (grant a
tenant access to a CyMed product). Dispatches through the real viewset (not
just the service layer) since what's being verified here is the
platform_admin-only permission gate itself — the one thing this feature
exists to add.
"""
import uuid

import pytest
from rest_framework.test import APIRequestFactory

from products.cymed.commercial.editions.models import (
    ProductCatalogEntry,
    ProductEdition,
    TenantProductSubscription,
)
from products.cymed.commercial.editions.views import TenantProductSubscriptionViewSet

PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def hospital_product(db):
    obj, _ = ProductCatalogEntry.objects.get_or_create(
        code="cymed_hospital",
        defaults={"tenant_id": PLATFORM_TENANT, "name": "CyMed Hospital", "is_active": True},
    )
    return obj


@pytest.fixture
def hospital_edition(db, hospital_product):
    obj, _ = ProductEdition.objects.get_or_create(
        product=hospital_product,
        code="community",
        defaults={
            "tenant_id": PLATFORM_TENANT, "name": "Community Hospital", "tier": "community",
            "is_active": True,
        },
    )
    return obj


@pytest.fixture
def enterprise_edition(db, hospital_product):
    obj, _ = ProductEdition.objects.get_or_create(
        product=hospital_product,
        code="enterprise_hospital",
        defaults={
            "tenant_id": PLATFORM_TENANT, "name": "Enterprise Hospital",
            "tier": "enterprise_hospital", "is_active": True,
        },
    )
    return obj


def _request(factory, path, data, roles):
    req = factory.post(path, data, format="json")
    req.user_session = {"user_id": "admin", "roles": roles}
    return req


class TestGrantAction:
    def test_non_admin_is_rejected(self, db, hospital_product, hospital_edition):
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"post": "grant"})
        target_tenant = str(uuid.uuid4())
        req = _request(
            factory,
            "/api/v1/commercial/editions/tenant-subscriptions/grant/",
            {"tenant_id": target_tenant, "product_code": "cymed_hospital", "edition_code": "community"},
            roles=["clinician"],
        )
        resp = view(req)
        assert resp.status_code == 403
        assert not TenantProductSubscription.objects.filter(tenant_id=target_tenant).exists()

    def test_platform_admin_can_grant_a_new_subscription(
        self, db, hospital_product, hospital_edition
    ):
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"post": "grant"})
        target_tenant = str(uuid.uuid4())
        req = _request(
            factory,
            "/api/v1/commercial/editions/tenant-subscriptions/grant/",
            {"tenant_id": target_tenant, "product_code": "cymed_hospital", "edition_code": "community"},
            roles=["platform_admin"],
        )
        resp = view(req)
        assert resp.status_code == 200
        sub = TenantProductSubscription.objects.get(tenant_id=target_tenant, product=hospital_product)
        assert sub.edition.code == "community"
        assert sub.is_active is True

    def test_granting_again_upgrades_in_place_not_duplicates(
        self, db, hospital_product, hospital_edition, enterprise_edition
    ):
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"post": "grant"})
        target_tenant = str(uuid.uuid4())
        TenantProductSubscription.objects.create(
            tenant_id=target_tenant, product=hospital_product, edition=hospital_edition,
            is_active=True,
        )
        req = _request(
            factory,
            "/api/v1/commercial/editions/tenant-subscriptions/grant/",
            {"tenant_id": target_tenant, "product_code": "cymed_hospital", "edition_code": "enterprise_hospital"},
            roles=["platform_admin"],
        )
        resp = view(req)
        assert resp.status_code == 200
        rows = TenantProductSubscription.objects.filter(tenant_id=target_tenant, product=hospital_product)
        assert rows.count() == 1
        assert rows.first().edition.code == "enterprise_hospital"

    def test_unknown_product_or_edition_is_rejected(self, db):
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"post": "grant"})
        req = _request(
            factory,
            "/api/v1/commercial/editions/tenant-subscriptions/grant/",
            {"tenant_id": str(uuid.uuid4()), "product_code": "no_such_product", "edition_code": "x"},
            roles=["platform_admin"],
        )
        resp = view(req)
        assert resp.status_code == 404

    def test_missing_fields_is_rejected(self, db):
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"post": "grant"})
        req = _request(
            factory,
            "/api/v1/commercial/editions/tenant-subscriptions/grant/",
            {"tenant_id": str(uuid.uuid4())},
            roles=["platform_admin"],
        )
        resp = view(req)
        assert resp.status_code == 400


class TestListPermission:
    def test_non_admin_cannot_list(self, db):
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"get": "list"})
        req = factory.get("/api/v1/commercial/editions/tenant-subscriptions/")
        req.user_session = {"user_id": "u", "roles": ["clinician"]}
        resp = view(req)
        assert resp.status_code == 403

    def test_platform_admin_sees_every_tenant(
        self, db, hospital_product, hospital_edition
    ):
        TenantProductSubscription.objects.create(
            tenant_id=uuid.uuid4(), product=hospital_product, edition=hospital_edition,
            is_active=True,
        )
        TenantProductSubscription.objects.create(
            tenant_id=uuid.uuid4(), product=hospital_product, edition=hospital_edition,
            is_active=True,
        )
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"get": "list"})
        req = factory.get("/api/v1/commercial/editions/tenant-subscriptions/")
        req.user_session = {"user_id": "admin", "roles": ["platform_admin"]}
        resp = view(req)
        assert resp.status_code == 200
        assert resp.data["count"] == 2
