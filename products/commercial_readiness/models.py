from django.db import models
from platform.common.models import BaseModel, PlatformModel


PLAN_TYPE_CHOICES = [
    ("per_user", "Per User"),
    ("per_bed", "Per Bed"),
    ("per_transaction", "Per Transaction"),
    ("flat_fee", "Flat Fee"),
    ("usage_based", "Usage Based"),
    ("enterprise", "Enterprise"),
]

BILLING_CYCLE_CHOICES = [
    ("monthly", "Monthly"),
    ("quarterly", "Quarterly"),
    ("annual", "Annual"),
    ("biennial", "Biennial"),
    ("one_time", "One Time"),
]

QUOTATION_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("sent", "Sent"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
    ("expired", "Expired"),
]

PROPOSAL_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("review", "Review"),
    ("submitted", "Submitted"),
    ("won", "Won"),
    ("lost", "Lost"),
]

COMPLIANCE_STANDARD_CHOICES = [
    ("hipaa", "HIPAA"),
    ("gdpr", "GDPR"),
    ("pdpl", "PDPL"),
    ("iso27001", "ISO 27001"),
    ("soc2", "SOC 2"),
    ("jcia", "JCIA"),
    ("cbahi", "CBAHI"),
    ("fhir_r4", "FHIR R4"),
    ("hl7_v2", "HL7 v2"),
    ("dicom", "DICOM"),
]

COMPLIANCE_STATUS_CHOICES = [
    ("certified", "Certified"),
    ("in_progress", "In Progress"),
    ("planned", "Planned"),
    ("not_applicable", "Not Applicable"),
]

BENCHMARK_CATEGORY_CHOICES = [
    ("features", "Features"),
    ("pricing", "Pricing"),
    ("performance", "Performance"),
    ("security", "Security"),
    ("compliance", "Compliance"),
    ("support", "Support"),
    ("scalability", "Scalability"),
]


class PricingPlan(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_pricing_plan"

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    product_code = models.CharField(max_length=50, db_index=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    min_units = models.PositiveIntegerField(default=1)
    max_units = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    country_codes = models.JSONField(default=list)

    def __str__(self):
        return f"{self.name} ({self.code}) — {self.plan_type}"


class Quotation(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_quotation"

    quote_number = models.CharField(max_length=100, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_organization = models.CharField(max_length=200, blank=True)
    sales_rep_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=QUOTATION_STATUS_CHOICES, default="draft")
    line_items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Quote {self.quote_number} — {self.customer_name} ({self.status})"


class Proposal(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_proposal"

    opportunity_id = models.CharField(max_length=100, db_index=True)
    customer_name = models.CharField(max_length=200)
    proposal_title = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=PROPOSAL_STATUS_CHOICES, default="draft")
    rfp_reference = models.CharField(max_length=200, blank=True)
    executive_summary = models.TextField(blank=True)
    solution_scope = models.JSONField(default=list)
    proposed_modules = models.JSONField(default=list)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    submission_date = models.DateField(null=True, blank=True)
    decision_date = models.DateField(null=True, blank=True)
    win_reason = models.TextField(blank=True)
    loss_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.proposal_title} — {self.customer_name} ({self.status})"


class LicenseKey(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_license_key"

    customer_id = models.UUIDField(db_index=True)
    product_code = models.CharField(max_length=50, db_index=True)
    edition = models.CharField(max_length=50, blank=True)
    key_value = models.CharField(max_length=200, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_users = models.PositiveIntegerField(null=True, blank=True)
    max_beds = models.PositiveIntegerField(null=True, blank=True)
    licensed_modules = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"License {self.key_value[:20]}... — {self.product_code}"


class ComplianceCertification(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_compliance_cert"

    product_code = models.CharField(max_length=50, db_index=True)
    standard = models.CharField(max_length=20, choices=COMPLIANCE_STANDARD_CHOICES)
    status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS_CHOICES, default="planned")
    certified_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    certificate_url = models.URLField(blank=True)
    auditor_name = models.CharField(max_length=200, blank=True)
    scope_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product_code} — {self.standard} ({self.status})"


class CompetitiveBenchmark(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_competitive_benchmark"

    product_code = models.CharField(max_length=50, db_index=True)
    competitor_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=BENCHMARK_CATEGORY_CHOICES)
    our_score = models.DecimalField(max_digits=4, decimal_places=1)
    competitor_score = models.DecimalField(max_digits=4, decimal_places=1)
    benchmark_notes = models.TextField(blank=True)
    last_updated = models.DateField()

    def __str__(self):
        return f"{self.product_code} vs {self.competitor_name} — {self.category}"


# ============================================================
# Program 6 – Commercial Platform Models
# ============================================================

from django.utils import timezone as tz

LICENSE_TYPE_CHOICES = [
    ("perpetual", "Perpetual"),
    ("subscription", "Subscription"),
    ("trial", "Trial"),
    ("evaluation", "Evaluation"),
    ("oem", "OEM"),
    ("floating", "Floating"),
]

LICENSE_SCOPE_CHOICES = [
    ("tenant", "Per Tenant"),
    ("facility", "Per Facility"),
    ("user", "Per User"),
    ("product", "Per Product"),
    ("enterprise", "Enterprise"),
    ("concurrent", "Concurrent Users"),
]

LICENSE_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("active", "Active"),
    ("suspended", "Suspended"),
    ("expired", "Expired"),
    ("revoked", "Revoked"),
    ("trial", "Trial"),
]

SUBSCRIPTION_STATUS_CHOICES = [
    ("trialing", "Trialing"),
    ("active", "Active"),
    ("past_due", "Past Due"),
    ("canceled", "Canceled"),
    ("paused", "Paused"),
]

EDITION_CODE_CHOICES = [
    ("starter", "Starter"),
    ("professional", "Professional"),
    ("enterprise", "Enterprise"),
    ("network", "Network"),
    ("government", "Government"),
]


class License(BaseModel):
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, default="subscription")
    license_scope = models.CharField(max_length=20, choices=LICENSE_SCOPE_CHOICES, default="tenant")
    status = models.CharField(max_length=20, choices=LICENSE_STATUS_CHOICES, default="pending")
    product_code = models.CharField(max_length=50, db_index=True)
    edition = models.CharField(max_length=50, blank=True)
    license_key = models.CharField(max_length=200, unique=True)
    issued_to = models.CharField(max_length=200)
    issued_to_email = models.EmailField()
    max_users = models.PositiveIntegerField(null=True, blank=True)
    max_concurrent = models.PositiveIntegerField(null=True, blank=True)
    max_facilities = models.PositiveIntegerField(null=True, blank=True)
    licensed_features = models.JSONField(default=list)
    licensed_modules = models.JSONField(default=list)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    grace_period_days = models.PositiveIntegerField(default=30)
    offline_token = models.CharField(max_length=500, blank=True)
    offline_valid_days = models.PositiveIntegerField(default=7)
    activated_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    parent_license = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="sub_licenses")
    notes = models.TextField(blank=True)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_license"

    @property
    def is_expired(self):
        if not self.valid_until:
            return False
        return tz.now() > self.valid_until

    @property
    def is_in_grace_period(self):
        if not self.valid_until:
            return False
        grace_end = self.valid_until + tz.timedelta(days=self.grace_period_days)
        return self.valid_until < tz.now() <= grace_end

    def generate_offline_token(self):
        import hashlib
        import json
        payload = {
            "license_key": self.license_key,
            "product_code": self.product_code,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "max_users": self.max_users,
            "licensed_features": sorted(self.licensed_features),
        }
        self.offline_token = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        return self.offline_token


class Subscription(BaseModel):
    license = models.OneToOneField(License, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(PricingPlan, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default="trialing")
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default="monthly")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    trial_end = models.DateField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    external_subscription_id = models.CharField(max_length=200, blank=True)
    payment_method_last4 = models.CharField(max_length=10, blank=True)
    billing_email = models.EmailField(blank=True)
    invoice_count = models.PositiveIntegerField(default=0)
    last_invoice_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_subscription"


class ProductEdition(PlatformModel):
    product_code = models.CharField(max_length=50, db_index=True)
    edition_code = models.CharField(max_length=20, choices=EDITION_CODE_CHOICES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    included_modules = models.JSONField(default=list)
    max_users_default = models.PositiveIntegerField(null=True, blank=True)
    min_users = models.PositiveIntegerField(default=1)
    support_level = models.CharField(max_length=50, blank=True)
    deployment_options = models.JSONField(default=list)
    highlighted_features = models.JSONField(default=list)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_product_edition"
        unique_together = [["product_code", "edition_code"]]
        ordering = ["product_code", "sort_order"]


class FeatureFlag(PlatformModel):
    product_code = models.CharField(max_length=50, db_index=True)
    edition_code = models.CharField(max_length=20, blank=True)
    flag_key = models.CharField(max_length=100)
    flag_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=True)
    enabled_for_editions = models.JSONField(default=list)
    overridable_per_tenant = models.BooleanField(default=False)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_feature_flag"
        unique_together = [["product_code", "flag_key"]]


class TenantFeatureFlagOverride(BaseModel):
    flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name="tenant_overrides")
    is_enabled = models.BooleanField()
    override_reason = models.CharField(max_length=200, blank=True)
    overridden_by_id = models.UUIDField(null=True, blank=True)
    overridden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_tenant_flag_override"


class WhiteLabelConfig(BaseModel):
    tenant_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    primary_color = models.CharField(max_length=20, blank=True)
    secondary_color = models.CharField(max_length=20, blank=True)
    accent_color = models.CharField(max_length=20, blank=True)
    logo_url = models.URLField(blank=True)
    favicon_url = models.URLField(blank=True)
    custom_domain = models.CharField(max_length=200, blank=True)
    login_page_bg_url = models.URLField(blank=True)
    email_from_name = models.CharField(max_length=200, blank=True)
    email_from_address = models.EmailField(blank=True)
    email_header_logo_url = models.URLField(blank=True)
    report_logo_url = models.URLField(blank=True)
    pdf_footer_text = models.CharField(max_length=300, blank=True)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_white_label_config"


class ConcurrentLicenseSession(BaseModel):
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="concurrent_sessions")
    user_id = models.UUIDField(db_index=True)
    device_fingerprint = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_concurrent_session"


class CustomerPortalAccess(BaseModel):
    user_id = models.UUIDField(db_index=True)
    access_level = models.CharField(
        max_length=20,
        choices=[("viewer", "Viewer"), ("standard", "Standard"), ("admin", "Admin")],
        default="standard",
    )
    can_manage_licenses = models.BooleanField(default=False)
    can_manage_billing = models.BooleanField(default=False)
    can_open_tickets = models.BooleanField(default=True)
    can_download_software = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_portal_access"


class SupportTicket(BaseModel):
    ticket_number = models.CharField(max_length=100, unique=True)
    submitted_by_id = models.UUIDField(db_index=True)
    subject = models.CharField(max_length=300)
    description = models.TextField()
    product_code = models.CharField(max_length=50, db_index=True)
    priority = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        default="medium",
    )
    status = models.CharField(
        max_length=30,
        choices=[
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("waiting_customer", "Waiting Customer"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        default="open",
    )
    assigned_to_id = models.UUIDField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    sla_due_at = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(default=list)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_support_ticket"
        ordering = ["-created_at"]


class MarketplaceListing(PlatformModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=30,
        choices=[
            ("module", "Module"),
            ("extension", "Extension"),
            ("theme", "Theme"),
            ("connector", "Connector"),
            ("ai_package", "AI Package"),
            ("clinical_template", "Clinical Template"),
            ("report", "Report"),
            ("dashboard", "Dashboard"),
        ],
    )
    product_codes = models.JSONField(default=list)
    publisher = models.CharField(max_length=200, blank=True)
    publisher_type = models.CharField(
        max_length=20,
        choices=[("official", "Official"), ("partner", "Partner"), ("community", "Community")],
        default="official",
    )
    version = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    icon_url = models.URLField(blank=True)
    screenshots_urls = models.JSONField(default=list)
    documentation_url = models.URLField(blank=True)
    price_model = models.CharField(
        max_length=20,
        choices=[("free", "Free"), ("one_time", "One Time"), ("subscription", "Subscription"), ("usage", "Usage Based")],
        default="free",
    )
    price_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(
        max_length=20,
        choices=[("draft", "Draft"), ("published", "Published"), ("deprecated", "Deprecated")],
        default="draft",
    )
    install_count = models.PositiveIntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    tags = models.JSONField(default=list)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_marketplace_listing"
        ordering = ["-is_featured", "-install_count"]


class MarketplaceInstallation(BaseModel):
    listing = models.ForeignKey(MarketplaceListing, on_delete=models.CASCADE, related_name="installations")
    installed_by_id = models.UUIDField()
    installed_version = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    installed_at = models.DateTimeField(auto_now_add=True)
    config = models.JSONField(default=dict)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_marketplace_installation"
        unique_together = [["tenant_id", "listing"]]


class CommercialMetricsSnapshot(PlatformModel):
    snapshot_date = models.DateField(db_index=True)
    metric_type = models.CharField(max_length=50)
    product_code = models.CharField(max_length=50, blank=True)
    value = models.DecimalField(max_digits=16, decimal_places=4)
    breakdown = models.JSONField(default=dict)

    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_metrics_snapshot"
        unique_together = [["snapshot_date", "metric_type", "product_code"]]
        ordering = ["-snapshot_date"]
