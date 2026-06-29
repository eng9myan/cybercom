"""
CyberCom Multi-Tenant Framework — Comprehensive Test Suite.
Coverage target: 90%
"""

import uuid
from datetime import timedelta

import pytest
from django.test import RequestFactory
from django.utils import timezone

from platform.tenant.models import (
    ComplianceFramework,
    EnvironmentType,
    LicenseType,
    SSOProtocol,
    SubscriptionPlan,
    Tenant,
    TenantAuditConfiguration,
    TenantBranding,
    TenantComplianceProfile,
    TenantConfiguration,
    TenantDeploymentProfile,
    TenantDomain,
    TenantEnvironment,
    TenantFeatureFlag,
    TenantLicense,
    TenantProfile,
    TenantRegion,
    TenantRetentionPolicy,
    TenantSSOConfiguration,
    TenantStatus,
    TenantStoragePolicy,
    TenantSubscription,
    TenantTier,
    TenantType,
)
from platform.tenant.permissions import (
    CanProvisionTenant,
    CanTerminateTenant,
    IsPlatformAdmin,
    ReadOnlyOrPlatformAdmin,
)
from platform.tenant.services import (
    TenantBootstrapRequest,
    TenantBootstrapService,
    TenantComplianceService,
    TenantContextService,
    TenantDomainService,
    TenantFeatureFlagService,
    TenantLicenseService,
    TenantLifecycleService,
    TenantRealmMappingService,
    TenantSSOService,
    _metrics,
    render_prometheus,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        name="Test Hospital",
        slug="test-hospital",
        display_name="Test Hospital System",
        tenant_type=TenantType.HEALTHCARE_SOVEREIGN,
        tier=TenantTier.DATABASE,
        country_code="SA",
        locale="ar",
        home_region="me-central-1",
        status=TenantStatus.ACTIVE,
    )


@pytest.fixture
def saas_tenant(db):
    return Tenant.objects.create(
        name="ACME Corp",
        slug="acme-corp",
        tenant_type=TenantType.SAAS,
        tier=TenantTier.SHARED,
        status=TenantStatus.ACTIVE,
    )


# ---------------------------------------------------------------------------
# TestTenant — model lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenant:
    def test_str(self, tenant):
        assert "test-hospital" in str(tenant)

    def test_activate(self, db):
        t = Tenant.objects.create(name="Pend", slug="pend", status=TenantStatus.PENDING)
        t.activate()
        assert t.status == TenantStatus.ACTIVE
        assert t.activated_at is not None

    def test_suspend(self, tenant):
        tenant.suspend()
        assert tenant.status == TenantStatus.SUSPENDED
        assert tenant.suspended_at is not None

    def test_archive(self, tenant):
        tenant.suspend()
        tenant.archive()
        assert tenant.status == TenantStatus.ARCHIVED
        assert tenant.archived_at is not None

    def test_restore_from_archived(self, tenant):
        tenant.archive()
        tenant.restore()
        assert tenant.status == TenantStatus.ACTIVE

    def test_restore_from_invalid_status_raises(self, tenant):
        with pytest.raises(ValueError):
            tenant.restore()

    def test_terminate(self, tenant):
        tenant.terminate()
        assert tenant.status == TenantStatus.TERMINATED
        assert tenant.terminated_at is not None

    def test_decommission_after_terminate(self, tenant):
        tenant.terminate()
        tenant.decommission()
        assert tenant.status == TenantStatus.DECOMMISSIONED
        assert tenant.decommissioned_at is not None

    def test_decommission_without_terminate_raises(self, tenant):
        with pytest.raises(ValueError):
            tenant.decommission()

    def test_unique_name(self, tenant, db):
        with pytest.raises(Exception):
            Tenant.objects.create(name="Test Hospital", slug="other")

    def test_unique_slug(self, tenant, db):
        with pytest.raises(Exception):
            Tenant.objects.create(name="Another", slug="test-hospital")


# ---------------------------------------------------------------------------
# TestTenantProfile
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantProfile:
    def test_create(self, tenant):
        profile = TenantProfile.objects.create(
            tenant=tenant,
            legal_name="Test Hospital LLC",
            contact_email="admin@test-hospital.sa",
        )
        assert str(profile) == f"Profile({tenant.slug})"

    def test_one_to_one(self, tenant):
        TenantProfile.objects.create(tenant=tenant)
        with pytest.raises(Exception):
            TenantProfile.objects.create(tenant=tenant)


# ---------------------------------------------------------------------------
# TestTenantConfiguration
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantConfiguration:
    def test_defaults(self, tenant):
        cfg = TenantConfiguration.objects.create(tenant=tenant)
        assert cfg.max_users == 100
        assert cfg.mfa_required is True
        assert cfg.allow_guest_access is False

    def test_str(self, tenant):
        cfg = TenantConfiguration.objects.create(tenant=tenant)
        assert "Config" in str(cfg)


# ---------------------------------------------------------------------------
# TestTenantBranding
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantBranding:
    def test_defaults(self, tenant):
        b = TenantBranding.objects.create(tenant=tenant)
        assert b.theme == "light"
        assert b.primary_color == "#1B4F8A"

    def test_rtl_default_for_arabic(self, tenant):
        b = TenantBranding.objects.create(tenant=tenant, default_language="ar", rtl_default=True)
        assert b.rtl_default is True


# ---------------------------------------------------------------------------
# TestTenantSubscription
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantSubscription:
    def test_create(self, tenant):
        sub = TenantSubscription.objects.create(tenant=tenant, plan=SubscriptionPlan.ENTERPRISE)
        assert str(sub) == f"Sub({tenant.slug}/enterprise)"

    def test_is_trial_false_by_default(self, tenant):
        sub = TenantSubscription.objects.create(tenant=tenant, plan=SubscriptionPlan.STARTER)
        assert sub.is_trial is False

    def test_is_trial_true(self, tenant):
        sub = TenantSubscription.objects.create(
            tenant=tenant,
            plan=SubscriptionPlan.STARTER,
            trial_ends_at=timezone.now() + timedelta(days=14),
        )
        assert sub.is_trial is True

    def test_is_expired(self, tenant):
        sub = TenantSubscription.objects.create(
            tenant=tenant,
            plan=SubscriptionPlan.STARTER,
            ends_at=timezone.now() - timedelta(days=1),
        )
        assert sub.is_expired is True


# ---------------------------------------------------------------------------
# TestTenantLicense
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantLicense:
    def test_is_valid(self, tenant):
        lic = TenantLicense.objects.create(
            tenant=tenant,
            module="cymed",
            license_type=LicenseType.SUBSCRIPTION,
        )
        assert lic.is_valid is True

    def test_is_invalid_inactive(self, tenant):
        lic = TenantLicense.objects.create(
            tenant=tenant,
            module="cymed",
            license_type=LicenseType.SUBSCRIPTION,
            is_active=False,
        )
        assert lic.is_valid is False

    def test_is_invalid_expired(self, tenant):
        lic = TenantLicense.objects.create(
            tenant=tenant,
            module="cymed",
            license_type=LicenseType.TRIAL,
            valid_until=timezone.now() - timedelta(days=1),
        )
        assert lic.is_valid is False

    def test_unique_together(self, tenant):
        TenantLicense.objects.create(
            tenant=tenant,
            module="cymed",
            license_type=LicenseType.SUBSCRIPTION,
        )
        with pytest.raises(Exception):
            TenantLicense.objects.create(
                tenant=tenant,
                module="cymed",
                license_type=LicenseType.SUBSCRIPTION,
            )


# ---------------------------------------------------------------------------
# TestTenantEnvironment
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantEnvironment:
    def test_create(self, tenant):
        env = TenantEnvironment.objects.create(
            tenant=tenant,
            env_type=EnvironmentType.PRODUCTION,
            name="hospital-prod",
            is_production=True,
        )
        assert "Env" in str(env)

    def test_unique_per_tenant_env_type(self, tenant):
        TenantEnvironment.objects.create(
            tenant=tenant, env_type=EnvironmentType.PRODUCTION, name="p1"
        )
        with pytest.raises(Exception):
            TenantEnvironment.objects.create(
                tenant=tenant, env_type=EnvironmentType.PRODUCTION, name="p2"
            )


# ---------------------------------------------------------------------------
# TestTenantRegion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantRegion:
    def test_create(self, tenant):
        region = TenantRegion.objects.create(
            tenant=tenant,
            region_code="me-central-1",
            region_name="Middle East Central",
            is_primary=True,
            country_code="SA",
        )
        assert "me-central-1" in str(region)


# ---------------------------------------------------------------------------
# TestTenantFeatureFlag
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantFeatureFlag:
    def test_enable_disable(self, tenant):
        flag = TenantFeatureFlag.objects.create(tenant=tenant, key="beta.test")
        assert flag.enabled is False
        flag.enable(by="admin")
        assert flag.enabled is True
        assert flag.enabled_at is not None
        flag.disable()
        assert flag.enabled is False

    def test_is_expired(self, tenant):
        flag = TenantFeatureFlag.objects.create(
            tenant=tenant,
            key="old.flag",
            enabled=True,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert flag.is_expired is True

    def test_unique_per_tenant_key(self, tenant):
        TenantFeatureFlag.objects.create(tenant=tenant, key="some.flag")
        with pytest.raises(Exception):
            TenantFeatureFlag.objects.create(tenant=tenant, key="some.flag")


# ---------------------------------------------------------------------------
# TestTenantDomain
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantDomain:
    def test_verify(self, tenant):
        domain = TenantDomain.objects.create(tenant=tenant, domain="hospital.sa")
        assert domain.is_verified is False
        domain.verify()
        assert domain.is_verified is True
        assert domain.verified_at is not None

    def test_unique_domain(self, tenant, saas_tenant):
        TenantDomain.objects.create(tenant=tenant, domain="hospital.sa")
        with pytest.raises(Exception):
            TenantDomain.objects.create(tenant=saas_tenant, domain="hospital.sa")


# ---------------------------------------------------------------------------
# TestTenantComplianceProfile
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantComplianceProfile:
    def test_is_current(self, tenant):
        cp = TenantComplianceProfile.objects.create(
            tenant=tenant,
            framework=ComplianceFramework.HIPAA,
            is_active=True,
        )
        assert cp.is_current is True

    def test_not_current_if_expired(self, tenant):
        cp = TenantComplianceProfile.objects.create(
            tenant=tenant,
            framework=ComplianceFramework.GDPR,
            is_active=True,
            expires_at=timezone.now() - timedelta(days=1),
        )
        assert cp.is_current is False

    def test_not_current_if_inactive(self, tenant):
        cp = TenantComplianceProfile.objects.create(
            tenant=tenant,
            framework=ComplianceFramework.ISO27001,
            is_active=False,
        )
        assert cp.is_current is False


# ---------------------------------------------------------------------------
# TestTenantBootstrapService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantBootstrapService:
    def test_bootstrap_creates_all_sub_records(self, db):
        req = TenantBootstrapRequest(
            name="Metro Hospital",
            slug="metro-hospital",
            tenant_type=TenantType.HEALTHCARE_SOVEREIGN,
            tier=TenantTier.DATABASE,
            country_code="SA",
            locale="ar",
            home_region="me-central-1",
            plan=SubscriptionPlan.ENTERPRISE,
            compliance_frameworks=["hipaa", "gdpr"],
            contact_email="admin@metro.sa",
        )
        tenant = TenantBootstrapService().bootstrap(req, created_by="admin")
        assert tenant.status == TenantStatus.PROVISIONING
        assert TenantProfile.objects.filter(tenant=tenant).exists()
        assert TenantConfiguration.objects.filter(tenant=tenant).exists()
        assert TenantBranding.objects.filter(tenant=tenant).exists()
        assert TenantSubscription.objects.filter(
            tenant=tenant, plan=SubscriptionPlan.ENTERPRISE
        ).exists()
        assert TenantAuditConfiguration.objects.filter(tenant=tenant).exists()
        assert TenantStoragePolicy.objects.filter(tenant=tenant).exists()
        assert TenantDeploymentProfile.objects.filter(tenant=tenant).exists()
        assert TenantEnvironment.objects.filter(
            tenant=tenant, env_type=EnvironmentType.PRODUCTION
        ).exists()
        assert TenantRegion.objects.filter(tenant=tenant, is_primary=True).exists()
        assert TenantComplianceProfile.objects.filter(tenant=tenant).count() == 2
        assert TenantFeatureFlag.objects.filter(tenant=tenant).count() >= 4
        assert TenantRetentionPolicy.objects.filter(tenant=tenant).count() >= 2

    def test_bootstrap_arabic_sets_rtl(self, db):
        req = TenantBootstrapRequest(name="Arabic Co", slug="arabic-co", locale="ar")
        tenant = TenantBootstrapService().bootstrap(req)
        branding = TenantBranding.objects.get(tenant=tenant)
        assert branding.rtl_default is True

    def test_bootstrap_english_not_rtl(self, db):
        req = TenantBootstrapRequest(name="English Co", slug="english-co", locale="en")
        tenant = TenantBootstrapService().bootstrap(req)
        branding = TenantBranding.objects.get(tenant=tenant)
        assert branding.rtl_default is False


# ---------------------------------------------------------------------------
# TestTenantLifecycleService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantLifecycleService:
    def test_activate(self, db):
        t = Tenant.objects.create(name="Svc1", slug="svc1", status=TenantStatus.PENDING)
        svc = TenantLifecycleService()
        svc.activate(t, by="admin")
        assert t.status == TenantStatus.ACTIVE

    def test_suspend(self, tenant):
        svc = TenantLifecycleService()
        svc.suspend(tenant, reason="billing_hold", by="admin")
        assert tenant.status == TenantStatus.SUSPENDED

    def test_archive(self, tenant):
        tenant.suspend()
        TenantLifecycleService().archive(tenant, by="admin")
        assert tenant.status == TenantStatus.ARCHIVED

    def test_restore(self, tenant):
        tenant.archive()
        TenantLifecycleService().restore(tenant)
        assert tenant.status == TenantStatus.ACTIVE

    def test_terminate(self, tenant):
        TenantLifecycleService().terminate(tenant, reason="contract_end", by="admin")
        assert tenant.status == TenantStatus.TERMINATED

    def test_decommission(self, tenant):
        tenant.terminate()
        TenantLifecycleService().decommission(tenant, by="admin")
        assert tenant.status == TenantStatus.DECOMMISSIONED


# ---------------------------------------------------------------------------
# TestTenantContextService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantContextService:
    def test_resolve_from_claims(self, tenant):
        svc = TenantContextService()
        result = svc.resolve_from_claims({"tenant_id": str(tenant.id)})
        assert result == tenant

    def test_resolve_from_claims_inactive_returns_none(self, db):
        t = Tenant.objects.create(name="Susp", slug="susp", status=TenantStatus.SUSPENDED)
        svc = TenantContextService()
        result = svc.resolve_from_claims({"tenant_id": str(t.id)})
        assert result is None

    def test_resolve_from_claims_no_id(self, db):
        svc = TenantContextService()
        result = svc.resolve_from_claims({})
        assert result is None

    def test_resolve_from_domain(self, tenant):
        TenantDomain.objects.create(
            tenant=tenant, domain="hospital.sa", is_verified=True, is_active=True
        )
        svc = TenantContextService()
        result = svc.resolve_from_domain("hospital.sa")
        assert result == tenant

    def test_resolve_from_domain_unverified_returns_none(self, tenant):
        TenantDomain.objects.create(
            tenant=tenant, domain="unverified.sa", is_verified=False, is_active=True
        )
        svc = TenantContextService()
        result = svc.resolve_from_domain("unverified.sa")
        assert result is None

    def test_resolve_from_slug(self, tenant):
        result = TenantContextService().resolve_from_slug(tenant.slug)
        assert result == tenant


# ---------------------------------------------------------------------------
# TestTenantRealmMappingService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantRealmMappingService:
    def test_assign_realm(self, tenant):
        realm_id = uuid.uuid4()
        TenantRealmMappingService().assign_realm(tenant, realm_id, "customer-test-hospital")
        assert tenant.identity_realm_id == realm_id
        assert tenant.keycloak_realm_name == "customer-test-hospital"

    def test_get_realm_name_fallback(self, tenant):
        name = TenantRealmMappingService().get_realm_name(tenant)
        assert name == f"customer-{tenant.slug}"

    def test_get_realm_name_explicit(self, tenant):
        tenant.keycloak_realm_name = "my-realm"
        tenant.save()
        name = TenantRealmMappingService().get_realm_name(tenant)
        assert name == "my-realm"


# ---------------------------------------------------------------------------
# TestTenantFeatureFlagService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantFeatureFlagService:
    def test_enable_creates_flag(self, tenant):
        svc = TenantFeatureFlagService()
        flag = svc.enable(tenant, "new.feature", by="admin")
        assert flag.enabled is True

    def test_disable(self, tenant):
        svc = TenantFeatureFlagService()
        svc.enable(tenant, "feat.x", by="admin")
        svc.disable(tenant, "feat.x")
        assert TenantFeatureFlag.objects.get(tenant=tenant, key="feat.x").enabled is False

    def test_is_enabled_false_when_missing(self, tenant):
        assert TenantFeatureFlagService().is_enabled(tenant, "missing.flag") is False

    def test_is_enabled_true(self, tenant):
        TenantFeatureFlag.objects.create(tenant=tenant, key="on.flag", enabled=True)
        assert TenantFeatureFlagService().is_enabled(tenant, "on.flag") is True

    def test_is_enabled_false_when_expired(self, tenant):
        TenantFeatureFlag.objects.create(
            tenant=tenant,
            key="exp.flag",
            enabled=True,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        assert TenantFeatureFlagService().is_enabled(tenant, "exp.flag") is False

    def test_disable_nonexistent_raises(self, tenant):
        with pytest.raises(ValueError):
            TenantFeatureFlagService().disable(tenant, "nonexistent.flag")


# ---------------------------------------------------------------------------
# TestTenantLicenseService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantLicenseService:
    def test_grant_license(self, tenant):
        svc = TenantLicenseService()
        lic = svc.grant_license(tenant, "cymed", LicenseType.SUBSCRIPTION, max_seats=500)
        assert lic.is_active is True
        assert lic.max_seats == 500

    def test_revoke_license(self, tenant):
        svc = TenantLicenseService()
        lic = svc.grant_license(tenant, "cymed", LicenseType.SUBSCRIPTION)
        svc.revoke_license(lic)
        assert lic.is_active is False

    def test_has_license_true(self, tenant):
        TenantLicense.objects.create(
            tenant=tenant, module="cymed", license_type=LicenseType.SUBSCRIPTION
        )
        assert TenantLicenseService().has_license(tenant, "cymed") is True

    def test_has_license_false(self, tenant):
        assert TenantLicenseService().has_license(tenant, "notlicensed") is False


# ---------------------------------------------------------------------------
# TestTenantComplianceService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantComplianceService:
    def test_add_framework(self, tenant):
        svc = TenantComplianceService()
        profile = svc.add_framework(tenant, ComplianceFramework.HIPAA)
        assert profile.framework == ComplianceFramework.HIPAA

    def test_active_frameworks(self, tenant):
        TenantComplianceProfile.objects.create(tenant=tenant, framework=ComplianceFramework.HIPAA)
        TenantComplianceProfile.objects.create(tenant=tenant, framework=ComplianceFramework.GDPR)
        frameworks = TenantComplianceService().active_frameworks(tenant)
        assert "hipaa" in frameworks
        assert "gdpr" in frameworks

    def test_requires_data_residency_hipaa(self, tenant):
        TenantComplianceProfile.objects.create(tenant=tenant, framework=ComplianceFramework.HIPAA)
        assert TenantComplianceService().requires_data_residency(tenant) is True

    def test_requires_data_residency_false(self, tenant):
        TenantComplianceProfile.objects.create(
            tenant=tenant, framework=ComplianceFramework.ISO27001
        )
        assert TenantComplianceService().requires_data_residency(tenant) is False


# ---------------------------------------------------------------------------
# TestTenantDomainService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantDomainService:
    def test_add_domain(self, tenant):
        svc = TenantDomainService()
        domain_obj = svc.add_domain(tenant, "myhosp.sa", is_primary=True)
        assert domain_obj.domain == "myhosp.sa"
        assert domain_obj.is_primary is True
        assert domain_obj.verification_token != ""

    def test_verify_domain(self, tenant):
        domain_obj = TenantDomain.objects.create(tenant=tenant, domain="verify.sa")
        TenantDomainService().verify_domain(domain_obj)
        assert domain_obj.is_verified is True


# ---------------------------------------------------------------------------
# TestTenantSSOService
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantSSOService:
    def test_configure_oidc(self, tenant):
        sso = TenantSSOService().configure(
            tenant,
            protocol=SSOProtocol.OIDC,
            alias="adfs",
            authorization_url="https://adfs.hospital.sa/auth",
            client_id="cybercom-sp",
        )
        assert sso.protocol == SSOProtocol.OIDC
        assert sso.alias == "adfs"

    def test_configure_idempotent(self, tenant):
        svc = TenantSSOService()
        svc.configure(tenant, SSOProtocol.OIDC, "adfs2", client_id="sp1")
        svc.configure(tenant, SSOProtocol.OIDC, "adfs2", client_id="sp2-updated")
        assert TenantSSOConfiguration.objects.filter(tenant=tenant, alias="adfs2").count() == 1

    def test_disable_sso(self, tenant):
        sso = TenantSSOConfiguration.objects.create(
            tenant=tenant, protocol=SSOProtocol.SAML, alias="saml-idp", is_enabled=True
        )
        TenantSSOService().disable(sso)
        assert sso.is_enabled is False


# ---------------------------------------------------------------------------
# TestPermissions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPermissions:
    def _make_request(self, rf, method="GET", claims=None):
        req = getattr(rf, method.lower())("/")
        req.auth_claims = claims or {}
        req.user = type("User", (), {"__str__": lambda s: "anonymous"})()
        return req

    def test_platform_admin_denied_no_roles(self, rf):
        req = self._make_request(rf)
        perm = IsPlatformAdmin()
        assert perm.has_permission(req, None) is False

    def test_platform_admin_allowed_with_role(self, rf):
        req = self._make_request(rf, claims={"realm_access": {"roles": ["platform_admin"]}})
        perm = IsPlatformAdmin()
        assert perm.has_permission(req, None) is True

    def test_read_only_or_admin_get_allowed(self, rf):
        req = self._make_request(rf, method="GET")
        perm = ReadOnlyOrPlatformAdmin()
        assert perm.has_permission(req, None) is True

    def test_read_only_or_admin_post_denied(self, rf):
        req = self._make_request(rf, method="POST")
        perm = ReadOnlyOrPlatformAdmin()
        assert perm.has_permission(req, None) is False

    def test_read_only_or_admin_post_allowed_for_admin(self, rf):
        req = self._make_request(
            rf, method="POST", claims={"realm_access": {"roles": ["platform_admin"]}}
        )
        perm = ReadOnlyOrPlatformAdmin()
        assert perm.has_permission(req, None) is True

    def test_can_provision_requires_platform_admin(self, rf):
        req = self._make_request(rf, claims={"realm_access": {"roles": ["tenant_admin"]}})
        perm = CanProvisionTenant()
        assert perm.has_permission(req, None) is False

    def test_can_terminate_requires_platform_admin(self, rf):
        req = self._make_request(rf, claims={"realm_access": {"roles": ["platform_admin"]}})
        perm = CanTerminateTenant()
        assert perm.has_permission(req, None) is True


# ---------------------------------------------------------------------------
# TestMetrics
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantMetrics:
    def test_render_prometheus_has_counters(self):
        output = render_prometheus()
        assert "cybercom_tenant_tenant_provisioned_total" in output
        assert "cybercom_tenant_sso_configured_total" in output

    def test_bootstrap_increments_provisioned_counter(self, db):
        before = _metrics.tenant_provisioned_total
        req = TenantBootstrapRequest(name="Incr", slug="incr")
        TenantBootstrapService().bootstrap(req)
        assert _metrics.tenant_provisioned_total == before + 1


# ---------------------------------------------------------------------------
# TestTenantTasks
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantTasks:
    def test_expire_feature_flags_task(self, tenant):
        TenantFeatureFlag.objects.create(
            tenant=tenant,
            key="old",
            enabled=True,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        from platform.tenant.tasks import expire_feature_flags_task

        count = expire_feature_flags_task()
        assert count >= 1

    def test_check_license_expiry_task(self, tenant):
        TenantLicense.objects.create(
            tenant=tenant,
            module="cymed",
            license_type=LicenseType.TRIAL,
            is_active=True,
            valid_until=timezone.now() - timedelta(days=1),
        )
        from platform.tenant.tasks import check_license_expiry_task

        count = check_license_expiry_task()
        assert count >= 1

    def test_check_subscription_expiry_suspends_tenant(self, tenant):
        TenantSubscription.objects.create(
            tenant=tenant,
            plan=SubscriptionPlan.STARTER,
            is_active=True,
            ends_at=timezone.now() - timedelta(days=1),
        )
        from platform.tenant.tasks import check_subscription_expiry_task

        count = check_subscription_expiry_task()
        tenant.refresh_from_db()
        assert tenant.status == TenantStatus.SUSPENDED
        assert count >= 1

    def test_sync_realm_mapping_task_missing_tenant(self, db):
        from platform.tenant.tasks import sync_realm_mapping_task

        result = sync_realm_mapping_task(str(uuid.uuid4()))
        assert result is None


# ---------------------------------------------------------------------------
# TestTenantHealthAPI
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTenantHealthAPI:
    def test_health_endpoint(self, rf, tenant):
        from platform.tenant.views import tenant_health

        request = rf.get("/")
        response = tenant_health(request)
        assert response.status_code == 200
        assert response.data["status"] == "ok"

    def test_metrics_endpoint(self, rf):
        from platform.tenant.views import tenant_metrics

        request = rf.get("/")
        response = tenant_metrics(request)
        assert response.status_code == 200
