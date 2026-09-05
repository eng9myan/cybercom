"""TenantViewSet.enable_flavor / .disable_flavor — the tenant-activation
half of the flavor engine (blueprint N); the registry/pack half is covered
in platform/canonical/tests/test_flavors.py."""

import uuid

import pytest
from rest_framework.test import APIClient

from platform.canonical import flavors
from platform.tenant.models import Tenant


@pytest.fixture
def admin_client(mint_token, mock_jwks):
    """No `tenant_id` claim and no X-Tenant-ID header: TenantIsolationMiddleware
    only clears `request.tenant_id` to None (unscoped, platform-wide access)
    for a `platform_admin` with neither — otherwise TenantViewSet.get_queryset
    would filter to `id=<claim>` and 404 every tenant this fixture didn't
    happen to create with a matching id."""
    client = APIClient()
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "admin@cybercom.io",
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = mint_token(payload)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestTenantFlavorActions:
    def test_enable_flavor_adds_registry_key(self, admin_client):
        flavors.sync_registry()
        tenant = Tenant.objects.create(name="Acme Retail", slug="acme-retail")

        resp = admin_client.post(f"/api/v1/tenants/{tenant.id}/enable-flavor/", {"key": "retail"})
        assert resp.status_code == 200
        assert resp.data["flavor_set"] == ["retail"]
        tenant.refresh_from_db()
        assert tenant.flavor_set == ["retail"]

    def test_enable_flavor_unknown_key_returns_404(self, admin_client):
        tenant = Tenant.objects.create(name="Acme2", slug="acme-2")
        resp = admin_client.post(
            f"/api/v1/tenants/{tenant.id}/enable-flavor/", {"key": "no-such-flavor"}
        )
        assert resp.status_code == 404
        tenant.refresh_from_db()
        assert tenant.flavor_set == []

    def test_enable_flavor_bad_key_format_returns_400(self, admin_client):
        tenant = Tenant.objects.create(name="Acme3", slug="acme-3")
        resp = admin_client.post(
            f"/api/v1/tenants/{tenant.id}/enable-flavor/", {"key": "not a slug!"}
        )
        assert resp.status_code == 400

    def test_disable_flavor_removes_key(self, admin_client):
        flavors.sync_registry()
        tenant = Tenant.objects.create(
            name="Acme4", slug="acme-4", flavor_set=["retail", "clinic"]
        )
        resp = admin_client.post(f"/api/v1/tenants/{tenant.id}/disable-flavor/", {"key": "retail"})
        assert resp.status_code == 200
        assert resp.data["flavor_set"] == ["clinic"]
        tenant.refresh_from_db()
        assert tenant.flavor_set == ["clinic"]

    def test_disable_flavor_is_a_safe_noop_for_unregistered_key(self, admin_client):
        tenant = Tenant.objects.create(name="Acme5", slug="acme-5")
        resp = admin_client.post(
            f"/api/v1/tenants/{tenant.id}/disable-flavor/", {"key": "never-enabled"}
        )
        assert resp.status_code == 200
        tenant.refresh_from_db()
        assert tenant.flavor_set == []
