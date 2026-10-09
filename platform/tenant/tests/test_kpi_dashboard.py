import uuid

import pytest
from django.apps import apps as django_apps
from rest_framework.test import APIClient

from platform.tenant.models import Tenant, TenantStatus, TenantSubscription, SubscriptionPlan

# platform.ephemeral_envs is only installed in platform's own test project and
# cycom (see views_kpi.py, which already degrades gracefully for this exact
# reason) — collecting this eagerly under e.g. cymed's settings module blows
# up with "doesn't declare an explicit app_label and isn't in INSTALLED_APPS"
# before any test even runs. Skip the whole module instead of hard-failing.
if not django_apps.is_installed("platform.ephemeral_envs"):
    pytest.skip(
        "platform.ephemeral_envs isn't installed under this settings module",
        allow_module_level=True,
    )

from platform.ephemeral_envs.models import EphemeralEnvironment  # noqa: E402


def _authed_client(mint_token, mock_jwks, *, roles, tenant_id=None, email="ops@cybercom.io"):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": email,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "realm_access": {"roles": roles},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestPlatformKpiDashboard:
    def test_non_platform_admin_is_refused(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, roles=["tenant_admin"], tenant_id=uuid.uuid4())
        resp = client.get("/api/v1/tenants/kpi-dashboard/")
        assert resp.status_code == 403

    def test_aggregates_real_counts_across_tenants(self, mint_token, mock_jwks):
        t1 = Tenant.objects.create(name="Acme", slug="acme", status=TenantStatus.ACTIVE, country_code="JO")
        t2 = Tenant.objects.create(name="Beta", slug="beta", status=TenantStatus.SUSPENDED, country_code="US")
        TenantSubscription.objects.create(tenant=t1, plan=SubscriptionPlan.ENTERPRISE, is_active=True)
        EphemeralEnvironment.objects.create(name="pr-1", app="cycom", status="ready")
        EphemeralEnvironment.objects.create(name="pr-2", app="cymed", status="failed")

        client = _authed_client(mint_token, mock_jwks, roles=["platform_admin"])
        resp = client.get("/api/v1/tenants/kpi-dashboard/")
        assert resp.status_code == 200
        data = resp.json()

        assert data["tenants"]["total"] >= 2
        assert data["tenants"]["by_status"]["active"] >= 1
        assert data["tenants"]["by_status"]["suspended"] >= 1
        assert data["active_subscriptions_by_plan"].get("enterprise", 0) >= 1
        assert data["einvoicing_coverage"].get("jo_jofotara", 0) >= 1
        assert data["einvoicing_coverage"].get("eu_peppol", 0) >= 1  # US -> Peppol since a0d99af6
        assert data["ephemeral_environments"]["total"] >= 2
        assert data["ephemeral_environments"]["by_status"].get("ready", 0) >= 1
        assert data["ephemeral_environments"]["by_status"].get("failed", 0) >= 1
