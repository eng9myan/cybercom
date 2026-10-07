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
from products.cymed.commercial.editions.views import (
    MyEntitlementsView,
    TenantProductSubscriptionViewSet,
)
from products.cymed.commercial.feature_flags.models import FeatureFlag
from products.cymed.commercial.feature_flags.services import FeatureFlagService

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
    # code="enterprise" matches the real seed data (0002_seed_catalog.py) and
    # EDITION_FEATURE_MAP's key "cymed_hospital:enterprise" — the `tier`
    # field's choice value ("enterprise_hospital") is a separate thing, not
    # the edition code.
    obj, _ = ProductEdition.objects.get_or_create(
        product=hospital_product,
        code="enterprise",
        defaults={
            "tenant_id": PLATFORM_TENANT, "name": "Enterprise Hospital",
            "tier": "enterprise_hospital", "is_active": True,
        },
    )
    return obj


@pytest.fixture
def hospital_icu_flag(db):
    # "hospital.icu" is seeded (0002_seed_flags) default_enabled=False, and is
    # only in HOSPITAL_ENTERPRISE_FEATURES, not the community tier — a clean
    # off-by-default feature to prove grant() actually flips something,
    # unlike community-tier features (e.g. hospital.adt) which are already
    # seeded default_enabled=True and would pass even with no wiring at all.
    obj, _ = FeatureFlag.objects.get_or_create(
        code="hospital.icu",
        defaults={
            "tenant_id": PLATFORM_TENANT, "name": "ICU", "scope": "edition",
            "default_enabled": False,
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
            {"tenant_id": target_tenant, "product_code": "cymed_hospital", "edition_code": "enterprise"},
            roles=["platform_admin"],
        )
        resp = view(req)
        assert resp.status_code == 200
        rows = TenantProductSubscription.objects.filter(tenant_id=target_tenant, product=hospital_product)
        assert rows.count() == 1
        assert rows.first().edition.code == "enterprise"

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

    def test_grant_also_enables_the_editions_feature_flags(
        self, db, hospital_product, hospital_edition, enterprise_edition, hospital_icu_flag
    ):
        """The product-boundary gate (TenantProductSubscription) is useless on
        its own if the ~37 ViewSets behind `required_feature` still reject
        the tenant — grant must also flip FeatureFlagService's switches."""
        factory = APIRequestFactory()
        view = TenantProductSubscriptionViewSet.as_view({"post": "grant"})
        target_tenant = str(uuid.uuid4())
        assert FeatureFlagService.is_enabled("hospital.icu", tenant_id=target_tenant) is False
        req = _request(
            factory,
            "/api/v1/commercial/editions/tenant-subscriptions/grant/",
            {"tenant_id": target_tenant, "product_code": "cymed_hospital", "edition_code": "enterprise"},
            roles=["platform_admin"],
        )
        resp = view(req)
        assert resp.status_code == 200
        assert FeatureFlagService.is_enabled("hospital.icu", tenant_id=target_tenant) is True

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


class TestMyEntitlementsView:
    def test_no_tenant_returns_empty(self, db):
        factory = APIRequestFactory()
        req = factory.get("/api/v1/commercial/editions/my-entitlements/")
        req.user_session = {"user_id": "u", "roles": ["physician"]}
        resp = MyEntitlementsView.as_view()(req)
        assert resp.status_code == 200
        assert resp.data == {"products": [], "legacy_full_access": False}

    def test_legacy_tenant_sees_every_active_product(self, db, hospital_product):
        factory = APIRequestFactory()
        req = factory.get("/api/v1/commercial/editions/my-entitlements/")
        req.user_session = {"user_id": "u", "roles": ["physician"]}
        req.tenant_id = uuid.uuid4()
        resp = MyEntitlementsView.as_view()(req)
        assert resp.status_code == 200
        assert resp.data["legacy_full_access"] is True
        assert "cymed_hospital" in resp.data["products"]

    def test_entitled_tenant_sees_only_subscribed_products(
        self, db, hospital_product, hospital_edition
    ):
        tenant_id = uuid.uuid4()
        TenantProductSubscription.objects.create(
            tenant_id=tenant_id, product=hospital_product, edition=hospital_edition, is_active=True,
        )
        factory = APIRequestFactory()
        req = factory.get("/api/v1/commercial/editions/my-entitlements/")
        req.user_session = {"user_id": "u", "roles": ["physician"]}
        req.tenant_id = tenant_id
        resp = MyEntitlementsView.as_view()(req)
        assert resp.status_code == 200
        assert resp.data == {"products": ["cymed_hospital"], "legacy_full_access": False}
