"""
CyberCom Multi-Tenant Framework — Domain Models.
ADR-0002: tiered multi-tenancy (T-Shared/T-Schema/T-DB/T-Cluster).
ADR-0005: IAM integration via CyIdentity realm mapping.
"""
import uuid
from django.db import models
from django.utils import timezone
from platform.common.models import PlatformModel


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class TenantTier(models.TextChoices):
    SHARED = "shared", "Shared Schema + RLS"
    SCHEMA = "schema", "Schema-per-Tenant"
    DATABASE = "database", "Database-per-Tenant"
    CLUSTER = "cluster", "Cluster-per-Tenant (Sovereign)"


class TenantType(models.TextChoices):
    SAAS = "saas", "SaaS (Shared)"
    DEDICATED = "dedicated", "Dedicated Database"
    DEDICATED_CLUSTER = "dedicated_cluster", "Dedicated Cluster"
    GOVERNMENT = "government", "Government Cloud"
    HEALTHCARE_SOVEREIGN = "healthcare_sovereign", "Healthcare Sovereign Cloud"
    ON_PREMISE = "on_premise", "On-Premise"


class TenantStatus(models.TextChoices):
    PROVISIONING = "provisioning", "Provisioning"
    PENDING = "pending", "Pending Activation"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"
    RESTORING = "restoring", "Restoring"
    TERMINATING = "terminating", "Terminating"
    TERMINATED = "terminated", "Terminated"
    DECOMMISSIONED = "decommissioned", "Decommissioned"


class SubscriptionPlan(models.TextChoices):
    STARTER = "starter", "Starter"
    PROFESSIONAL = "professional", "Professional"
    ENTERPRISE = "enterprise", "Enterprise"
    GOVERNMENT = "government", "Government"
    CUSTOM = "custom", "Custom"


class LicenseType(models.TextChoices):
    SUBSCRIPTION = "subscription", "Subscription"
    PERPETUAL = "perpetual", "Perpetual"
    TRIAL = "trial", "Trial"
    PARTNER = "partner", "Partner"
    INTERNAL = "internal", "Internal"


class EnvironmentType(models.TextChoices):
    PRODUCTION = "production", "Production"
    STAGING = "staging", "Staging"
    DEVELOPMENT = "development", "Development"
    TESTING = "testing", "Testing"
    DEMO = "demo", "Demo"


class SSOProtocol(models.TextChoices):
    OIDC = "oidc", "OpenID Connect"
    SAML = "saml", "SAML 2.0"
    LDAP = "ldap", "LDAP / Active Directory"


class ComplianceFramework(models.TextChoices):
    HIPAA = "hipaa", "HIPAA"
    GDPR = "gdpr", "GDPR"
    PDPL = "pdpl", "Saudi PDPL"
    UAE_DP = "uae_dp", "UAE Data Protection"
    JORDAN_DP = "jordan_dp", "Jordan Personal Data Protection"
    ISO27001 = "iso27001", "ISO 27001"
    SOC2 = "soc2", "SOC 2 Type II"
    PCI_DSS = "pci_dss", "PCI DSS"


# ---------------------------------------------------------------------------
# Tenant (central registry)
# ---------------------------------------------------------------------------

class Tenant(PlatformModel):
    """
    Central registry of all tenants. One row per organization.
    ADR-0002: source of truth for tenant identity and isolation tier.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200, blank=True)
    tenant_type = models.CharField(
        max_length=30, choices=TenantType.choices, default=TenantType.SAAS
    )
    tier = models.CharField(
        max_length=20, choices=TenantTier.choices, default=TenantTier.SHARED
    )
    status = models.CharField(
        max_length=20, choices=TenantStatus.choices, default=TenantStatus.PROVISIONING
    )

    country_code = models.CharField(max_length=2, default="SA")
    timezone = models.CharField(max_length=50, default="Asia/Riyadh")
    locale = models.CharField(max_length=10, default="ar")
    home_region = models.CharField(max_length=50, default="me-central-1")

    identity_realm_id = models.UUIDField(null=True, blank=True)
    keycloak_realm_name = models.CharField(max_length=100, blank=True)

    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    terminated_at = models.DateTimeField(null=True, blank=True)
    decommissioned_at = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_tenants"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["tenant_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"

    def activate(self) -> None:
        self.status = TenantStatus.ACTIVE
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "activated_at", "updated_at"])

    def suspend(self) -> None:
        self.status = TenantStatus.SUSPENDED
        self.suspended_at = timezone.now()
        self.save(update_fields=["status", "suspended_at", "updated_at"])

    def archive(self) -> None:
        self.status = TenantStatus.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])

    def restore(self) -> None:
        if self.status not in (TenantStatus.ARCHIVED, TenantStatus.SUSPENDED):
            raise ValueError(f"Cannot restore tenant in status {self.status}")
        self.status = TenantStatus.ACTIVE
        self.save(update_fields=["status", "updated_at"])

    def terminate(self) -> None:
        self.status = TenantStatus.TERMINATED
        self.terminated_at = timezone.now()
        self.save(update_fields=["status", "terminated_at", "updated_at"])

    def decommission(self) -> None:
        if self.status != TenantStatus.TERMINATED:
            raise ValueError("Must terminate before decommissioning")
        self.status = TenantStatus.DECOMMISSIONED
        self.decommissioned_at = timezone.now()
        self.save(update_fields=["status", "decommissioned_at", "updated_at"])


# ---------------------------------------------------------------------------
# TenantProfile
# ---------------------------------------------------------------------------

class TenantProfile(PlatformModel):
    """Extended organization profile — contact, legal, billing."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="profile")

    legal_name = models.CharField(max_length=300, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)

    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)

    billing_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)

    industry = models.CharField(max_length=100, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)
    website = models.URLField(blank=True)

    class Meta:
        db_table = "platform_tenant_profiles"

    def __str__(self) -> str:
        return f"Profile({self.tenant.slug})"


# ---------------------------------------------------------------------------
# TenantConfiguration
# ---------------------------------------------------------------------------

class TenantConfiguration(PlatformModel):
    """Runtime configuration — features, limits, data residency."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="configuration")

    max_users = models.PositiveIntegerField(default=100)
    max_api_calls_per_day = models.PositiveIntegerField(default=10000)
    max_storage_gb = models.PositiveIntegerField(default=50)
    max_realms = models.PositiveIntegerField(default=3)

    data_residency_region = models.CharField(max_length=50, default="me-central-1")
    data_residency_country = models.CharField(max_length=2, default="SA")
    cross_region_replication_allowed = models.BooleanField(default=False)

    byok_enabled = models.BooleanField(default=False)
    byok_key_arn = models.CharField(max_length=500, blank=True)

    mfa_required = models.BooleanField(default=True)
    session_timeout_seconds = models.PositiveIntegerField(default=900)
    idle_timeout_seconds = models.PositiveIntegerField(default=1800)

    audit_retention_days = models.PositiveIntegerField(default=90)
    log_shipping_enabled = models.BooleanField(default=False)
    log_destination = models.CharField(max_length=500, blank=True)

    allow_public_registration = models.BooleanField(default=False)
    allow_social_login = models.BooleanField(default=True)
    allow_guest_access = models.BooleanField(default=False)

    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_tenant_configurations"

    def __str__(self) -> str:
        return f"Config({self.tenant.slug})"


# ---------------------------------------------------------------------------
# TenantBranding
# ---------------------------------------------------------------------------

class TenantBranding(PlatformModel):
    """White-label branding — logos, colors, themes, RTL support."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="branding")

    primary_color = models.CharField(max_length=7, default="#1B4F8A")
    secondary_color = models.CharField(max_length=7, default="#00B4D8")
    accent_color = models.CharField(max_length=7, default="#90E0EF")
    background_color = models.CharField(max_length=7, default="#FFFFFF")
    text_color = models.CharField(max_length=7, default="#1A1A2E")

    logo_url = models.URLField(blank=True)
    logo_dark_url = models.URLField(blank=True)
    favicon_url = models.URLField(blank=True)

    app_name = models.CharField(max_length=100, blank=True)
    tagline = models.CharField(max_length=200, blank=True)

    theme = models.CharField(max_length=20, default="light", choices=[
        ("light", "Light"), ("dark", "Dark"), ("auto", "Auto")
    ])
    rtl_default = models.BooleanField(default=False)
    default_language = models.CharField(max_length=10, default="ar")
    supported_languages = models.JSONField(default=list)

    custom_css = models.TextField(blank=True)
    custom_login_html = models.TextField(blank=True)
    email_header_html = models.TextField(blank=True)
    email_footer_html = models.TextField(blank=True)

    class Meta:
        db_table = "platform_tenant_brandings"

    def __str__(self) -> str:
        return f"Branding({self.tenant.slug})"


# ---------------------------------------------------------------------------
# TenantSubscription
# ---------------------------------------------------------------------------

class TenantSubscription(PlatformModel):
    """Active subscription plan and billing cycle."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="subscriptions")

    plan = models.CharField(max_length=30, choices=SubscriptionPlan.choices)
    is_active = models.BooleanField(default=True)

    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    monthly_price_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    annual_price_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")

    external_subscription_id = models.CharField(max_length=200, blank=True)
    auto_renew = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "platform_tenant_subscriptions"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Sub({self.tenant.slug}/{self.plan})"

    @property
    def is_trial(self) -> bool:
        return self.trial_ends_at is not None and self.trial_ends_at > timezone.now()

    @property
    def is_expired(self) -> bool:
        return self.ends_at is not None and self.ends_at < timezone.now()


# ---------------------------------------------------------------------------
# TenantLicense
# ---------------------------------------------------------------------------

class TenantLicense(PlatformModel):
    """Module licensing — what the tenant is licensed to run."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="licenses")

    module = models.CharField(max_length=100)
    license_type = models.CharField(max_length=30, choices=LicenseType.choices)
    edition = models.CharField(max_length=50, blank=True)

    max_seats = models.PositiveIntegerField(null=True, blank=True)
    max_transactions = models.PositiveIntegerField(null=True, blank=True)

    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    license_key = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_tenant_licenses"
        unique_together = [("tenant", "module", "license_type")]
        ordering = ["-valid_from"]

    def __str__(self) -> str:
        return f"License({self.tenant.slug}/{self.module})"

    @property
    def is_valid(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return now >= self.valid_from


# ---------------------------------------------------------------------------
# TenantEnvironment
# ---------------------------------------------------------------------------

class TenantEnvironment(PlatformModel):
    """
    Per-tenant environment instance (prod, staging, dev, etc.).
    ADR-0012: dev/test/stage/prod topology mirroring.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="environments")

    env_type = models.CharField(max_length=20, choices=EnvironmentType.choices)
    name = models.CharField(max_length=100)
    region = models.CharField(max_length=50, default="me-central-1")
    namespace = models.CharField(max_length=200, blank=True)
    cluster_id = models.CharField(max_length=200, blank=True)
    database_name = models.CharField(max_length=200, blank=True)
    database_schema = models.CharField(max_length=200, blank=True)

    is_active = models.BooleanField(default=True)
    is_production = models.BooleanField(default=False)

    api_base_url = models.URLField(blank=True)
    keycloak_realm = models.CharField(max_length=100, blank=True)

    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_tenant_environments"
        unique_together = [("tenant", "env_type")]

    def __str__(self) -> str:
        return f"Env({self.tenant.slug}/{self.env_type})"


# ---------------------------------------------------------------------------
# TenantRegion
# ---------------------------------------------------------------------------

class TenantRegion(PlatformModel):
    """Data residency region assignments for a tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="regions")

    region_code = models.CharField(max_length=50)
    region_name = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    is_dr = models.BooleanField(default=False)
    country_code = models.CharField(max_length=2)

    data_types = models.JSONField(default=list, blank=True)

    enabled_at = models.DateTimeField(default=timezone.now)
    disabled_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_tenant_regions"
        unique_together = [("tenant", "region_code")]

    def __str__(self) -> str:
        return f"Region({self.tenant.slug}/{self.region_code})"


# ---------------------------------------------------------------------------
# TenantDeploymentProfile
# ---------------------------------------------------------------------------

class TenantDeploymentProfile(PlatformModel):
    """Kubernetes / infrastructure deployment parameters for the tenant."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="deployment_profile")

    helm_values = models.JSONField(default=dict, blank=True)
    resource_cpu_request = models.CharField(max_length=20, default="250m")
    resource_cpu_limit = models.CharField(max_length=20, default="1000m")
    resource_memory_request = models.CharField(max_length=20, default="256Mi")
    resource_memory_limit = models.CharField(max_length=20, default="1Gi")

    replica_count = models.PositiveIntegerField(default=2)
    hpa_min_replicas = models.PositiveIntegerField(default=2)
    hpa_max_replicas = models.PositiveIntegerField(default=20)

    node_selector = models.JSONField(default=dict, blank=True)
    tolerations = models.JSONField(default=list, blank=True)
    affinity = models.JSONField(default=dict, blank=True)

    image_pull_secret = models.CharField(max_length=200, blank=True)
    service_account = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "platform_tenant_deployment_profiles"

    def __str__(self) -> str:
        return f"DeployProfile({self.tenant.slug})"


# ---------------------------------------------------------------------------
# TenantFeatureFlag
# ---------------------------------------------------------------------------

class TenantFeatureFlag(PlatformModel):
    """Per-tenant feature toggles — module enablement, beta features."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="feature_flags")

    key = models.CharField(max_length=200)
    enabled = models.BooleanField(default=False)
    value = models.JSONField(default=None, null=True, blank=True)
    description = models.TextField(blank=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "platform_tenant_feature_flags"
        unique_together = [("tenant", "key")]
        ordering = ["key"]

    def __str__(self) -> str:
        state = "on" if self.enabled else "off"
        return f"Flag({self.tenant.slug}/{self.key}={state})"

    def enable(self, by: str = "") -> None:
        self.enabled = True
        self.enabled_at = timezone.now()
        self.created_by = by or self.created_by
        self.save(update_fields=["enabled", "enabled_at", "created_by", "updated_at"])

    def disable(self) -> None:
        self.enabled = False
        self.save(update_fields=["enabled", "updated_at"])

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at < timezone.now()


# ---------------------------------------------------------------------------
# TenantDomain
# ---------------------------------------------------------------------------

class TenantDomain(PlatformModel):
    """Custom domains mapped to the tenant (for CNAME / TLS termination)."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="domains")

    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    ssl_enabled = models.BooleanField(default=True)
    ssl_cert_expires_at = models.DateTimeField(null=True, blank=True)
    ssl_provider = models.CharField(max_length=50, default="lets_encrypt")

    verification_token = models.CharField(max_length=200, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    dns_record_type = models.CharField(max_length=10, default="CNAME")
    dns_target = models.CharField(max_length=253, blank=True)

    class Meta:
        db_table = "platform_tenant_domains"
        ordering = ["-is_primary", "domain"]

    def __str__(self) -> str:
        return f"Domain({self.domain}->{self.tenant.slug})"

    def verify(self) -> None:
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=["is_verified", "verified_at", "updated_at"])


# ---------------------------------------------------------------------------
# TenantSSOConfiguration
# ---------------------------------------------------------------------------

class TenantSSOConfiguration(PlatformModel):
    """Identity federation / SSO per tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="sso_configurations")

    protocol = models.CharField(max_length=10, choices=SSOProtocol.choices)
    alias = models.CharField(max_length=100)
    display_name = models.CharField(max_length=200, blank=True)
    is_enabled = models.BooleanField(default=True)

    authorization_url = models.URLField(blank=True)
    token_url = models.URLField(blank=True)
    userinfo_url = models.URLField(blank=True)
    jwks_url = models.URLField(blank=True)
    client_id = models.CharField(max_length=200, blank=True)
    client_secret_hint = models.CharField(max_length=4, blank=True)
    scopes = models.JSONField(default=list)

    entity_id = models.CharField(max_length=500, blank=True)
    sso_url = models.URLField(blank=True)
    slo_url = models.URLField(blank=True)
    x509_cert = models.TextField(blank=True)

    ldap_url = models.CharField(max_length=500, blank=True)
    bind_dn = models.CharField(max_length=500, blank=True)
    base_dn = models.CharField(max_length=500, blank=True)
    user_filter = models.CharField(max_length=500, blank=True)

    keycloak_provider_id = models.CharField(max_length=200, blank=True)
    attribute_mapping = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_tenant_sso_configurations"
        unique_together = [("tenant", "alias")]

    def __str__(self) -> str:
        return f"SSO({self.tenant.slug}/{self.alias})"


# ---------------------------------------------------------------------------
# TenantStoragePolicy
# ---------------------------------------------------------------------------

class TenantStoragePolicy(PlatformModel):
    """Storage limits, quotas, and data residency for tenant data."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="storage_policy")

    max_storage_gb = models.PositiveIntegerField(default=50)
    max_file_size_mb = models.PositiveIntegerField(default=100)
    allowed_file_types = models.JSONField(default=list)

    storage_backend = models.CharField(max_length=50, default="s3")
    bucket_name = models.CharField(max_length=200, blank=True)
    bucket_region = models.CharField(max_length=50, blank=True)
    encryption_key_id = models.CharField(max_length=500, blank=True)

    versioning_enabled = models.BooleanField(default=True)
    lifecycle_rules = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "platform_tenant_storage_policies"

    def __str__(self) -> str:
        return f"StoragePolicy({self.tenant.slug})"


# ---------------------------------------------------------------------------
# TenantRetentionPolicy
# ---------------------------------------------------------------------------

class TenantRetentionPolicy(PlatformModel):
    """Data retention schedule per data category and compliance requirement."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="retention_policies")

    data_category = models.CharField(max_length=100)
    retention_days = models.PositiveIntegerField()
    deletion_strategy = models.CharField(max_length=50, default="hard_delete", choices=[
        ("hard_delete", "Hard Delete"),
        ("soft_delete", "Soft Delete"),
        ("anonymize", "Anonymize"),
        ("archive", "Archive to Cold Storage"),
    ])
    legal_hold = models.BooleanField(default=False)
    compliance_basis = models.CharField(max_length=50, choices=ComplianceFramework.choices, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_tenant_retention_policies"
        unique_together = [("tenant", "data_category")]

    def __str__(self) -> str:
        return f"Retention({self.tenant.slug}/{self.data_category}/{self.retention_days}d)"


# ---------------------------------------------------------------------------
# TenantComplianceProfile
# ---------------------------------------------------------------------------

class TenantComplianceProfile(PlatformModel):
    """Active compliance frameworks and certification status."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="compliance_profiles")

    framework = models.CharField(max_length=20, choices=ComplianceFramework.choices)
    is_active = models.BooleanField(default=True)
    certified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    certification_body = models.CharField(max_length=200, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    scope_description = models.TextField(blank=True)
    controls_implemented = models.JSONField(default=list, blank=True)
    last_audit_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "platform_tenant_compliance_profiles"
        unique_together = [("tenant", "framework")]

    def __str__(self) -> str:
        return f"Compliance({self.tenant.slug}/{self.framework})"

    @property
    def is_current(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


# ---------------------------------------------------------------------------
# TenantAuditConfiguration
# ---------------------------------------------------------------------------

class TenantAuditConfiguration(PlatformModel):
    """Per-tenant audit logging settings — what to capture, where to ship."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="audit_configuration")

    capture_login_events = models.BooleanField(default=True)
    capture_data_access = models.BooleanField(default=True)
    capture_admin_actions = models.BooleanField(default=True)
    capture_api_calls = models.BooleanField(default=False)
    capture_config_changes = models.BooleanField(default=True)

    hot_retention_days = models.PositiveIntegerField(default=90)
    cold_retention_years = models.PositiveIntegerField(default=7)

    siem_enabled = models.BooleanField(default=False)
    siem_endpoint = models.URLField(blank=True)
    siem_format = models.CharField(max_length=20, default="json", choices=[
        ("json", "JSON"), ("cef", "CEF"), ("leef", "LEEF"), ("syslog", "Syslog")
    ])
    siem_token_hint = models.CharField(max_length=4, blank=True)

    export_enabled = models.BooleanField(default=False)
    export_bucket = models.CharField(max_length=200, blank=True)
    export_schedule_cron = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "platform_tenant_audit_configurations"

    def __str__(self) -> str:
        return f"AuditConfig({self.tenant.slug})"
