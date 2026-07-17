"""
CyberCom Multi-Tenant Framework — Service Layer.
ADR-0002: tiered multi-tenancy; ADR-0005: CyIdentity realm mapping.
"""

import logging
import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from platform.events.models import OutboxEvent
from platform.tenant.models import (
    EnvironmentType,
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

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tenant Metrics
# ---------------------------------------------------------------------------


class TenantMetrics:
    """In-process counters for Prometheus exposition."""

    tenant_provisioned_total: int = 0
    tenant_activated_total: int = 0
    tenant_suspended_total: int = 0
    tenant_terminated_total: int = 0
    tenant_decommissioned_total: int = 0
    sso_configured_total: int = 0
    domain_verified_total: int = 0
    feature_flag_toggled_total: int = 0
    compliance_profile_added_total: int = 0
    realm_mapped_total: int = 0


_metrics = TenantMetrics()


def render_prometheus() -> str:
    lines = []
    for attr, val in vars(_metrics).items():
        lines.append(f"cybercom_tenant_{attr} {val}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Tenant Event Emitter
# ---------------------------------------------------------------------------


class TenantEventEmitter:
    @staticmethod
    def emit(event_type: str, tenant: Tenant, payload: dict) -> None:
        try:
            OutboxEvent.objects.create(
                tenant_id=tenant.id,
                topic="platform.tenant.events",
                event_type=event_type,
                payload={**payload, "tenant_slug": tenant.slug},
            )
        except Exception:
            log.exception("Failed to emit tenant event %s for %s", event_type, tenant.slug)


# ---------------------------------------------------------------------------
# TenantBootstrapService — full provisioning wizard
# ---------------------------------------------------------------------------


@dataclass
class TenantBootstrapRequest:
    name: str
    slug: str
    tenant_type: str = TenantType.SAAS
    tier: str = TenantTier.SHARED
    country_code: str = "SA"
    locale: str = "ar"
    home_region: str = "me-central-1"
    plan: str = SubscriptionPlan.PROFESSIONAL
    compliance_frameworks: list = field(default_factory=list)
    contact_email: str = ""
    display_name: str = ""


class TenantBootstrapService:
    """
    Orchestrates full tenant provisioning:
    Tenant → Profile → Configuration → Branding → Subscription →
    AuditConfiguration → StoragePolicy → DeploymentProfile → Environments
    """

    @transaction.atomic
    def bootstrap(self, req: TenantBootstrapRequest, created_by: str = "") -> Tenant:
        tenant = Tenant.objects.create(
            name=req.name,
            slug=req.slug,
            display_name=req.display_name or req.name,
            tenant_type=req.tenant_type,
            tier=req.tier,
            country_code=req.country_code,
            locale=req.locale,
            home_region=req.home_region,
            status=TenantStatus.PROVISIONING,
        )

        TenantProfile.objects.create(
            tenant=tenant,
            contact_email=req.contact_email,
        )

        TenantConfiguration.objects.create(
            tenant=tenant,
            data_residency_region=req.home_region,
            data_residency_country=req.country_code,
        )

        TenantBranding.objects.create(
            tenant=tenant,
            rtl_default=(req.locale in ("ar", "he", "fa", "ur")),
            default_language=req.locale,
        )

        TenantSubscription.objects.create(
            tenant=tenant,
            plan=req.plan,
            is_active=True,
        )

        TenantAuditConfiguration.objects.create(tenant=tenant)
        TenantStoragePolicy.objects.create(
            tenant=tenant,
            bucket_region=req.home_region,
        )
        TenantDeploymentProfile.objects.create(tenant=tenant)

        TenantEnvironment.objects.create(
            tenant=tenant,
            env_type=EnvironmentType.PRODUCTION,
            name=f"{req.slug}-prod",
            region=req.home_region,
            is_production=True,
        )

        TenantRegion.objects.create(
            tenant=tenant,
            region_code=req.home_region,
            region_name=req.home_region,
            is_primary=True,
            country_code=req.country_code,
        )

        for framework in req.compliance_frameworks:
            TenantComplianceProfile.objects.create(
                tenant=tenant,
                framework=framework,
            )

        self._seed_default_feature_flags(tenant)
        self._seed_default_retention_policies(tenant, req.compliance_frameworks)

        _metrics.tenant_provisioned_total += 1
        TenantEventEmitter.emit(
            "tenant.provisioned",
            tenant,
            {
                "tier": tenant.tier,
                "tenant_type": tenant.tenant_type,
                "created_by": created_by,
            },
        )

        log.info("Tenant %s provisioned (tier=%s)", tenant.slug, tenant.tier)
        return tenant

    def _seed_default_feature_flags(self, tenant: Tenant) -> None:
        defaults = [
            ("cyidentity.enabled", True),
            ("audit.enabled", True),
            ("notifications.enabled", True),
            ("api.rate_limiting.enabled", True),
            ("beta.ai_assist", False),
        ]
        for key, enabled in defaults:
            TenantFeatureFlag.objects.get_or_create(
                tenant=tenant,
                key=key,
                defaults={"enabled": enabled},
            )

    def _seed_default_retention_policies(self, tenant: Tenant, frameworks: list) -> None:
        policies = [
            ("audit_logs", 2555, "archive", ""),
            ("user_data", 365, "anonymize", "gdpr" if "gdpr" in frameworks else ""),
            ("medical_records", 3650, "archive", "hipaa" if "hipaa" in frameworks else ""),
            ("session_data", 90, "hard_delete", ""),
        ]
        for category, days, strategy, basis in policies:
            TenantRetentionPolicy.objects.get_or_create(
                tenant=tenant,
                data_category=category,
                defaults={
                    "retention_days": days,
                    "deletion_strategy": strategy,
                    "compliance_basis": basis,
                },
            )


# ---------------------------------------------------------------------------
# DemoProvisioningService — self-serve 7-day trial tenants
# ---------------------------------------------------------------------------

DEMO_TRIAL_HOURS = 24 * 7

# Products whose cycom-erp-style frontend can't yet resolve an arbitrary
# per-tenant realm at login time (single fixed-realm login flow) — for these,
# reuse the shared "cybercom" realm (bootstrapped by bootstrap_platform_realm)
# instead of provisioning a brand new per-tenant realm. The demo user still
# gets its own fresh tenant_id as a Keycloak user *attribute*, which is what
# actually ends up in the issued JWT's tenant_id claim — that's the only
# thing Cycom's tenant-scoped querysets trust, so isolation still holds even
# though the realm itself is shared. Known, accepted trade-off: the
# UserProfile mirror row's own tenant_id column will reflect the shared
# realm's sentinel tenant_id, not this demo tenant's — cosmetic only, nothing
# authorization-relevant reads that column.
SHARED_REALM_PRODUCTS = {"cycom"}
SHARED_REALM_NAME = "cybercom"


class DemoProvisioningService:
    """
    Public self-serve demo signup: a real, fully isolated Tenant (same
    bootstrap chain as a paying customer) plus a real CyIdentity realm/user,
    both torn down automatically once the trial expires
    (see expire_demo_tenants_task in platform.tenant.tasks).
    """

    @transaction.atomic
    def provision_demo(
        self, *, product_code: str, email: str, org_name: str = "", locale: str = "en"
    ) -> tuple[Tenant, "UserProfile | None"]:
        # cyshop has its own completely separate, unfederated auth system (no
        # CyIdentity/Keycloak trust) — adapter approach: call cyshop's own
        # registration endpoint service-to-service instead of routing it
        # through RealmService/UserProvisioningService like every other product.
        if product_code == "cyshop":
            return self._provision_demo_cyshop(email=email, org_name=org_name, locale=locale)

        from platform.cyidentity.models import IdentityRealm
        from platform.cyidentity.services import ClientService, RealmService, UserProvisioningService

        suffix = secrets.token_hex(4)
        slug = f"demo-{product_code}-{suffix}".replace("_", "-")[:100]
        display_name = org_name or f"Demo — {product_code}"
        # Tenant.name is globally unique — display_name is not, so the
        # suffix only needs to live in the DB-unique field.
        unique_name = f"{display_name} ({suffix})"

        bootstrap_req = TenantBootstrapRequest(
            name=unique_name,
            slug=slug,
            tenant_type=TenantType.SAAS,
            tier=TenantTier.SHARED,
            locale=locale,
            plan=SubscriptionPlan.STARTER,
            contact_email=email,
            display_name=display_name,
        )
        tenant = TenantBootstrapService().bootstrap(bootstrap_req, created_by="demo_signup")

        trial_ends_at = timezone.now() + timedelta(hours=DEMO_TRIAL_HOURS)
        # is_expired reads ends_at, is_trial reads trial_ends_at — set both so
        # the same expiry timestamp flips both properties together.
        TenantSubscription.objects.filter(tenant=tenant).update(
            trial_ends_at=trial_ends_at, ends_at=trial_ends_at
        )

        tenant.metadata = {**tenant.metadata, "is_demo": True, "product_code": product_code}
        tenant.save(update_fields=["metadata", "updated_at"])

        if product_code in SHARED_REALM_PRODUCTS:
            realm = IdentityRealm.objects.get(realm_name=SHARED_REALM_NAME)
        else:
            realm_name = f"demo-{slug}"
            realm = RealmService().provision(
                tenant_id=tenant.id,
                realm_name=realm_name,
                realm_type="customer",
                display_name=display_name,
                locale=locale,
            )
            # RealmService.provision() only creates the realm itself — no
            # OIDC client. Without one, no demo user in a freshly-provisioned
            # per-tenant realm has ever been able to actually log in via
            # password grant (confirmed: every non-shared-realm demo realm
            # up to now had zero registered clients). Public (no secret) so
            # any consuming frontend can do direct grant with just
            # client_id/username/password — no secret to hand to a browser.
            ClientService().register(
                realm,
                client_id="cybercom-backend",
                name="CyberCom Backend",
                public_client=True,
                direct_access_grants_enabled=True,
                mfa_required=False,
            )
        TenantRealmMappingService().assign_realm(tenant, realm.id, realm.realm_name)

        username = email.split("@")[0] + "-" + suffix
        # Keycloak's realm User Profile marks firstName/lastName as required
        # attributes. Leaving them blank doesn't block user creation, but
        # Keycloak dynamically evaluates VERIFY_PROFILE as needed the moment
        # the user tries to log in — and direct/password grant has no
        # browser to resolve that interactively, so every demo user ever
        # created without these has failed login with a generic
        # "Account is not fully set up" (resolve_required_actions).
        user = UserProvisioningService().provision_user(
            realm,
            username=username,
            email=email,
            first_name=(org_name.split(" ")[0] if org_name else "Demo"),
            last_name="Trial Account",
            enabled=True,
            email_verified=False,
            attributes={"tenant_id": [str(tenant.id)], "product_code": [product_code]},
        )
        # provision_user() always sets a real password now (previously none was
        # ever set, so demo logins were unusable) — surface it via the tenant's
        # transient result so the view can return it to the signup response.
        tenant.demo_password = getattr(user, "plaintext_password", None)

        TenantLifecycleService().activate(tenant)

        TenantEventEmitter.emit(
            "tenant.demo_provisioned",
            tenant,
            {"product_code": product_code, "trial_ends_at": trial_ends_at.isoformat()},
        )
        log.info("Demo tenant %s provisioned for product=%s", tenant.slug, product_code)
        return tenant, user

    def _provision_demo_cyshop(
        self, *, email: str, org_name: str = "", locale: str = "en"
    ) -> tuple[Tenant, None]:
        """
        cyshop adapter: calls cyshop's own TenantRegisterView (a single atomic
        call on cyshop's side that creates its Tenant/Company/Branch/User)
        instead of going through CyIdentity. Mirrors provision_demo()'s naming
        pattern locally, tracks the resulting tenant on the platform side too
        (for cross-product admin visibility), but does NOT set up a Keycloak
        realm/user — there isn't one for cyshop.

        Known gap, not solved here: cyshop's own Tenant/TenantSettings model
        has no trial/expiry field at all (confirmed — only a subscription_status
        choice that includes TRIAL but nothing sets or enforces it, no
        trial_ends_at). The platform-side TenantSubscription below still gets
        a real trial_ends_at for admin-panel visibility, but nothing currently
        acts on it for cyshop the way expire_demo_tenants_task does for
        Keycloak-backed products — an expired cyshop demo tenant today just
        keeps working. Deliberately not building a teardown call against
        cyshop for this: that would mean adding a new admin/deactivation
        endpoint to cyshop's own codebase, out of scope for the "adapter, not
        migration" approach this phase committed to.
        """
        import re

        import httpx

        suffix = secrets.token_hex(4)
        display_name = org_name or f"Demo Cyshop {suffix}"
        subdomain_base = re.sub(r"[^a-z0-9]+", "-", (org_name or "demo-cyshop").lower()).strip("-") or "demo-cyshop"
        subdomain = f"{subdomain_base}-{suffix}"[:63]
        username = email.split("@")[0] + "-" + suffix
        password = secrets.token_urlsafe(16)

        cyshop_base = os.environ.get("CYSHOP_BACKEND_URL", "http://localhost:8020")
        resp = httpx.post(
            f"{cyshop_base}/api/v1/tenants/register/",
            json={
                "name": display_name,
                "subdomain": subdomain,
                "email": email,
                "username": username,
                "password": password,
            },
            timeout=15,
        )
        resp.raise_for_status()
        cyshop_payload = resp.json()

        trial_ends_at = timezone.now() + timedelta(hours=DEMO_TRIAL_HOURS)
        bootstrap_req = TenantBootstrapRequest(
            name=f"{display_name} ({suffix})",
            slug=f"demo-cyshop-{suffix}",
            tenant_type=TenantType.SAAS,
            tier=TenantTier.SHARED,
            locale=locale,
            plan=SubscriptionPlan.STARTER,
            contact_email=email,
            display_name=display_name,
        )
        tenant = TenantBootstrapService().bootstrap(bootstrap_req, created_by="demo_signup")
        TenantSubscription.objects.filter(tenant=tenant).update(
            trial_ends_at=trial_ends_at, ends_at=trial_ends_at
        )
        tenant.metadata = {
            **tenant.metadata,
            "is_demo": True,
            "product_code": "cyshop",
            "cyshop_tenant_id": cyshop_payload.get("tenant_id"),
            "cyshop_subdomain": subdomain,
        }
        tenant.save(update_fields=["metadata", "updated_at"])
        tenant.demo_password = password
        tenant.demo_username = username
        tenant.demo_subdomain = subdomain

        TenantLifecycleService().activate(tenant)
        TenantEventEmitter.emit(
            "tenant.demo_provisioned",
            tenant,
            {"product_code": "cyshop", "trial_ends_at": trial_ends_at.isoformat()},
        )
        log.info("Demo cyshop tenant %s provisioned (subdomain=%s)", tenant.slug, subdomain)
        return tenant, None


# ---------------------------------------------------------------------------
# TenantLifecycleService
# ---------------------------------------------------------------------------


class TenantLifecycleService:
    def activate(self, tenant: Tenant, by: str = "") -> Tenant:
        tenant.activate()
        _metrics.tenant_activated_total += 1
        TenantEventEmitter.emit("tenant.activated", tenant, {"by": by})
        return tenant

    def suspend(self, tenant: Tenant, reason: str = "", by: str = "") -> Tenant:
        tenant.suspend()
        _metrics.tenant_suspended_total += 1
        TenantEventEmitter.emit("tenant.suspended", tenant, {"reason": reason, "by": by})
        return tenant

    def archive(self, tenant: Tenant, by: str = "") -> Tenant:
        tenant.archive()
        TenantEventEmitter.emit("tenant.archived", tenant, {"by": by})
        return tenant

    def restore(self, tenant: Tenant, by: str = "") -> Tenant:
        tenant.restore()
        TenantEventEmitter.emit("tenant.restored", tenant, {"by": by})
        return tenant

    def terminate(self, tenant: Tenant, reason: str = "", by: str = "") -> Tenant:
        tenant.terminate()
        _metrics.tenant_terminated_total += 1
        TenantEventEmitter.emit("tenant.terminated", tenant, {"reason": reason, "by": by})
        return tenant

    def decommission(self, tenant: Tenant, by: str = "") -> Tenant:
        tenant.decommission()
        _metrics.tenant_decommissioned_total += 1
        TenantEventEmitter.emit("tenant.decommissioned", tenant, {"by": by})
        return tenant


# ---------------------------------------------------------------------------
# TenantContextService — tenant resolution from request
# ---------------------------------------------------------------------------


class TenantContextService:
    """
    Resolves the active tenant from a request.
    Resolution order: JWT claim > X-Tenant-ID header > domain lookup > slug path.
    """

    def resolve_from_claims(self, claims: dict) -> Tenant | None:
        tenant_id = claims.get("tenant_id") or claims.get("tid")
        if not tenant_id:
            return None
        try:
            return Tenant.objects.get(id=tenant_id, status=TenantStatus.ACTIVE)
        except Tenant.DoesNotExist:
            return None

    def resolve_from_header(self, header_value: str) -> Tenant | None:
        if not header_value:
            return None
        try:
            return Tenant.objects.get(id=header_value, status=TenantStatus.ACTIVE)
        except (Tenant.DoesNotExist, Exception):
            return None

    def resolve_from_domain(self, host: str) -> Tenant | None:
        if not host:
            return None
        from platform.tenant.models import TenantDomain

        try:
            td = TenantDomain.objects.select_related("tenant").get(
                domain=host.lower(), is_verified=True, is_active=True
            )
            return td.tenant if td.tenant.status == TenantStatus.ACTIVE else None
        except TenantDomain.DoesNotExist:
            return None

    def resolve_from_slug(self, slug: str) -> Tenant | None:
        try:
            return Tenant.objects.get(slug=slug, status=TenantStatus.ACTIVE)
        except Tenant.DoesNotExist:
            return None


# ---------------------------------------------------------------------------
# TenantRealmMappingService — CyIdentity integration
# ---------------------------------------------------------------------------


class TenantRealmMappingService:
    """Links a CyIdentity IdentityRealm to the tenant record."""

    def assign_realm(self, tenant: Tenant, realm_id: uuid.UUID, realm_name: str) -> Tenant:
        tenant.identity_realm_id = realm_id
        tenant.keycloak_realm_name = realm_name
        tenant.save(update_fields=["identity_realm_id", "keycloak_realm_name", "updated_at"])
        _metrics.realm_mapped_total += 1
        TenantEventEmitter.emit(
            "tenant.realm.created",
            tenant,
            {
                "realm_id": str(realm_id),
                "realm_name": realm_name,
            },
        )
        return tenant

    def get_realm_name(self, tenant: Tenant) -> str:
        return tenant.keycloak_realm_name or f"customer-{tenant.slug}"


# ---------------------------------------------------------------------------
# TenantSSOService
# ---------------------------------------------------------------------------


class TenantSSOService:
    def configure(
        self, tenant: Tenant, protocol: str, alias: str, **kwargs
    ) -> TenantSSOConfiguration:
        sso, _ = TenantSSOConfiguration.objects.update_or_create(
            tenant=tenant,
            alias=alias,
            defaults={"protocol": protocol, **kwargs},
        )
        _metrics.sso_configured_total += 1
        TenantEventEmitter.emit(
            "tenant.sso.configured", tenant, {"alias": alias, "protocol": protocol}
        )
        return sso

    def disable(self, sso: TenantSSOConfiguration) -> TenantSSOConfiguration:
        sso.is_enabled = False
        sso.save(update_fields=["is_enabled", "updated_at"])
        return sso


# ---------------------------------------------------------------------------
# TenantDomainService
# ---------------------------------------------------------------------------


class TenantDomainService:
    def add_domain(self, tenant: Tenant, domain: str, is_primary: bool = False) -> TenantDomain:
        import secrets

        token = secrets.token_urlsafe(32)
        td = TenantDomain.objects.create(
            tenant=tenant,
            domain=domain.lower(),
            is_primary=is_primary,
            verification_token=token,
        )
        return td

    def verify_domain(self, domain_obj: TenantDomain) -> TenantDomain:
        domain_obj.verify()
        _metrics.domain_verified_total += 1
        TenantEventEmitter.emit(
            "tenant.domain.verified", domain_obj.tenant, {"domain": domain_obj.domain}
        )
        return domain_obj


# ---------------------------------------------------------------------------
# TenantFeatureFlagService
# ---------------------------------------------------------------------------


class TenantFeatureFlagService:
    def is_enabled(self, tenant: Tenant, key: str) -> bool:
        try:
            flag = TenantFeatureFlag.objects.get(tenant=tenant, key=key)
            return flag.enabled and not flag.is_expired
        except TenantFeatureFlag.DoesNotExist:
            return False

    def enable(self, tenant: Tenant, key: str, by: str = "", value=None) -> TenantFeatureFlag:
        flag, _ = TenantFeatureFlag.objects.get_or_create(tenant=tenant, key=key)
        flag.value = value
        flag.enable(by=by)
        _metrics.feature_flag_toggled_total += 1
        TenantEventEmitter.emit("tenant.feature.enabled", tenant, {"key": key, "by": by})
        return flag

    def disable(self, tenant: Tenant, key: str) -> TenantFeatureFlag:
        try:
            flag = TenantFeatureFlag.objects.get(tenant=tenant, key=key)
            flag.disable()
            _metrics.feature_flag_toggled_total += 1
            return flag
        except TenantFeatureFlag.DoesNotExist:
            raise ValueError(f"Feature flag {key} not found for tenant {tenant.slug}")


# ---------------------------------------------------------------------------
# TenantLicenseService
# ---------------------------------------------------------------------------


class TenantLicenseService:
    def grant_license(
        self,
        tenant: Tenant,
        module: str,
        license_type: str,
        valid_until=None,
        max_seats: int | None = None,
        **kwargs,
    ) -> TenantLicense:
        lic, _ = TenantLicense.objects.update_or_create(
            tenant=tenant,
            module=module,
            license_type=license_type,
            defaults={
                "is_active": True,
                "valid_until": valid_until,
                "max_seats": max_seats,
                **kwargs,
            },
        )
        TenantEventEmitter.emit(
            "tenant.license.updated",
            tenant,
            {
                "module": module,
                "license_type": license_type,
            },
        )
        return lic

    def revoke_license(self, lic: TenantLicense) -> TenantLicense:
        lic.is_active = False
        lic.save(update_fields=["is_active", "updated_at"])
        TenantEventEmitter.emit("tenant.license.revoked", lic.tenant, {"module": lic.module})
        return lic

    def has_license(self, tenant: Tenant, module: str) -> bool:
        return (
            TenantLicense.objects.filter(tenant=tenant, module=module, is_active=True)
            .filter(Q(valid_until__isnull=True) | Q(valid_until__gt=timezone.now()))
            .exists()
        )


# ---------------------------------------------------------------------------
# TenantComplianceService
# ---------------------------------------------------------------------------


class TenantComplianceService:
    def add_framework(self, tenant: Tenant, framework: str, **kwargs) -> TenantComplianceProfile:
        profile, _ = TenantComplianceProfile.objects.update_or_create(
            tenant=tenant,
            framework=framework,
            defaults={"is_active": True, **kwargs},
        )
        _metrics.compliance_profile_added_total += 1
        TenantEventEmitter.emit("tenant.compliance.added", tenant, {"framework": framework})
        return profile

    def active_frameworks(self, tenant: Tenant) -> list:
        return list(
            TenantComplianceProfile.objects.filter(tenant=tenant, is_active=True).values_list(
                "framework", flat=True
            )
        )

    def requires_data_residency(self, tenant: Tenant) -> bool:
        sensitive = {"hipaa", "gdpr", "pdpl", "uae_dp", "jordan_dp"}
        return bool(sensitive & set(self.active_frameworks(tenant)))
