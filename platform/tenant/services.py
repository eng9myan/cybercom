"""
CyberCom Multi-Tenant Framework — Service Layer.
ADR-0002: tiered multi-tenancy; ADR-0005: CyIdentity realm mapping.
"""

import logging
import uuid
from dataclasses import dataclass, field

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
                aggregate_type="tenant",
                aggregate_id=str(tenant.id),
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
