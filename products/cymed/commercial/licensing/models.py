import uuid
import hashlib
import hmac
from django.db import models
from platform.common.models import BaseModel


class LicenseServer(BaseModel):
    """Optional centralized license validation server record."""
    name = models.CharField(max_length=255)
    server_url = models.URLField(max_length=500, blank=True)
    public_key_pem = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_commercial_license_servers"

    def __str__(self):
        return self.name


class License(BaseModel):
    """Master license record for a customer deployment."""
    LICENSE_TYPES = [
        ("trial", "Trial"),
        ("subscription", "Subscription"),
        ("annual", "Annual"),
        ("multi_year", "Multi-Year"),
        ("enterprise", "Enterprise"),
        ("government", "Government"),
        ("perpetual", "Perpetual"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("revoked", "Revoked"),
        ("grace", "Grace Period"),
        ("suspended", "Suspended"),
    ]
    DELIVERY_MODES = [
        ("online", "Online"),
        ("offline", "Offline"),
        ("air_gapped", "Air-Gapped"),
        ("government", "Government"),
    ]

    # Identity
    license_number = models.CharField(max_length=100, unique=True)
    product_code = models.CharField(max_length=100)         # e.g. "cymed_clinic", "cymed_hospital"
    edition_code = models.CharField(max_length=100)         # e.g. "starter", "enterprise"
    license_type = models.CharField(max_length=50, choices=LICENSE_TYPES, default="subscription")
    delivery_mode = models.CharField(max_length=50, choices=DELIVERY_MODES, default="online")

    # Customer
    customer_id = models.UUIDField(null=True, blank=True)
    organization_name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=10)          # ISO 3166-1 alpha-2

    # Validity
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)   # null = perpetual
    grace_period_days = models.PositiveIntegerField(default=14)

    # Limits
    max_users = models.PositiveIntegerField(default=0)      # 0 = unlimited
    max_providers = models.PositiveIntegerField(default=0)
    max_beds = models.PositiveIntegerField(default=0)
    max_facilities = models.PositiveIntegerField(default=0)
    max_api_calls_per_day = models.PositiveIntegerField(default=0)

    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="active")
    is_multi_tenant = models.BooleanField(default=False)

    # Signature (for offline/air-gapped validation)
    signature_hash = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = "cymed_commercial_licenses"

    def __str__(self):
        return f"{self.license_number} ({self.organization_name})"

    def compute_signature(self, secret: str) -> str:
        payload = f"{self.license_number}:{self.product_code}:{self.edition_code}:{self.organization_name}:{self.valid_from}:{self.valid_until}"
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def is_valid(self) -> bool:
        from django.utils import timezone
        today = timezone.now().date()
        if self.status == "revoked":
            return False
        if self.valid_until and today > self.valid_until:
            import datetime
            if today > self.valid_until + datetime.timedelta(days=self.grace_period_days):
                return False
            self.status = "grace"
        return self.status in ("active", "grace")


class LicenseKey(BaseModel):
    """Activation key associated with a license."""
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="keys")
    key_string = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)
    is_revoked = models.BooleanField(default=False)
    max_activations = models.PositiveIntegerField(default=1)
    activation_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_commercial_license_keys"

    def can_activate(self) -> bool:
        return not self.is_revoked and self.activation_count < self.max_activations


class LicenseActivation(BaseModel):
    """Record of a license key activation event."""
    license_key = models.ForeignKey(LicenseKey, on_delete=models.CASCADE, related_name="activations")
    activated_at = models.DateTimeField(auto_now_add=True)
    machine_fingerprint = models.CharField(max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    deployment_profile_code = models.CharField(max_length=100, blank=True)
    is_online = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_commercial_license_activations"


class LicenseFeature(BaseModel):
    """Per-license feature entitlement overrides."""
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="features")
    feature_code = models.CharField(max_length=200)
    is_enabled = models.BooleanField(default=True)
    limit_value = models.PositiveIntegerField(null=True, blank=True)   # e.g. max templates = 5
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_commercial_license_features"
        unique_together = [("license", "feature_code")]


class LicenseAudit(BaseModel):
    """Immutable audit log for all license lifecycle events."""
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="audit_log")
    event_type = models.CharField(max_length=100)   # activated, renewed, revoked, expired, grace_started
    performed_by = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_commercial_license_audit"
        ordering = ["-logged_at"]


class LicenseUsage(BaseModel):
    """Daily snapshot of license consumption metrics."""
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="usage_records")
    snapshot_date = models.DateField()
    active_users = models.PositiveIntegerField(default=0)
    active_providers = models.PositiveIntegerField(default=0)
    active_beds = models.PositiveIntegerField(default=0)
    api_calls = models.PositiveIntegerField(default=0)
    storage_gb = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    is_over_limit = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_commercial_license_usage"
        unique_together = [("license", "snapshot_date")]


class OfflineActivationPackage(BaseModel):
    """Air-gapped / offline activation bundle."""
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="offline_packages")
    package_token = models.CharField(max_length=512, unique=True)
    machine_fingerprint = models.CharField(max_length=512)
    signed_payload = models.TextField()                # Base64-encoded signed JSON
    is_consumed = models.BooleanField(default=False)
    consumed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "cymed_commercial_offline_packages"
