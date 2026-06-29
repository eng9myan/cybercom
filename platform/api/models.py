"""
CyberCom API Framework — Domain Models.
ADR-0003: REST + OpenAPI 3.1. ADR-0030: API Governance.
"""

import hashlib
import secrets
import uuid

from django.db import models
from django.utils import timezone

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ApiStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    DEPRECATED = "deprecated", "Deprecated"
    RETIRED = "retired", "Retired"
    SUSPENDED = "suspended", "Suspended"


class ApiClassification(models.TextChoices):
    PUBLIC = "public", "Public"
    PARTNER = "partner", "Partner"
    INTERNAL = "internal", "Internal"
    PRIVATE = "private", "Private"
    FHIR = "fhir", "FHIR Clinical"
    GOVERNMENT = "government", "Government"


class ApiKeyStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"
    SUSPENDED = "suspended", "Suspended"


class WebhookStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    FAILED = "failed", "Failed"
    DISABLED = "disabled", "Disabled"


class WebhookDeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    RETRYING = "retrying", "Retrying"
    DEAD = "dead", "Dead Letter"


class VersionLifecycle(models.TextChoices):
    ALPHA = "alpha", "Alpha"
    BETA = "beta", "Beta"
    STABLE = "stable", "Stable"
    DEPRECATED = "deprecated", "Deprecated"
    RETIRED = "retired", "Retired"


class HttpMethod(models.TextChoices):
    GET = "GET", "GET"
    POST = "POST", "POST"
    PUT = "PUT", "PUT"
    PATCH = "PATCH", "PATCH"
    DELETE = "DELETE", "DELETE"


class RateLimitScope(models.TextChoices):
    TENANT = "tenant", "Per Tenant"
    USER = "user", "Per User"
    APPLICATION = "application", "Per Application"
    GLOBAL = "global", "Global"
    IP = "ip", "Per IP"


# ---------------------------------------------------------------------------
# ApiVersion
# ---------------------------------------------------------------------------


class ApiVersion(models.Model):
    """Tracks API semantic versions and their lifecycle per ADR-0030 S3.4."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    major = models.PositiveSmallIntegerField(default=1)
    minor = models.PositiveSmallIntegerField(default=0)
    patch = models.PositiveSmallIntegerField(default=0)
    lifecycle = models.CharField(
        max_length=20, choices=VersionLifecycle.choices, default=VersionLifecycle.STABLE
    )
    release_notes = models.TextField(blank=True)
    deprecated_at = models.DateTimeField(null=True, blank=True)
    sunset_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_api_versions"
        unique_together = [("major", "minor", "patch")]
        ordering = ["-major", "-minor", "-patch"]

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch} ({self.lifecycle})"

    @property
    def version_string(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    @property
    def is_deprecated(self) -> bool:
        return self.lifecycle in (VersionLifecycle.DEPRECATED, VersionLifecycle.RETIRED)

    def deprecate(self, sunset_at=None) -> None:
        self.lifecycle = VersionLifecycle.DEPRECATED
        self.deprecated_at = timezone.now()
        self.sunset_at = sunset_at
        self.save(update_fields=["lifecycle", "deprecated_at", "sunset_at"])


# ---------------------------------------------------------------------------
# ApiCatalog
# ---------------------------------------------------------------------------


class ApiCatalog(models.Model):
    """Registry of all CyberCom APIs. Each entry = one API product."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    classification = models.CharField(max_length=20, choices=ApiClassification.choices)
    status = models.CharField(max_length=20, choices=ApiStatus.choices, default=ApiStatus.DRAFT)
    owner_team = models.CharField(max_length=100, blank=True)
    base_path = models.CharField(max_length=200)
    current_version = models.ForeignKey(
        ApiVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name="catalogs"
    )
    openapi_schema = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list)
    requires_auth = models.BooleanField(default=True)
    fhir_resource = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_api_catalog"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"Api({self.slug}, {self.classification})"

    def publish(self) -> None:
        self.status = ApiStatus.ACTIVE
        self.save(update_fields=["status", "updated_at"])

    def deprecate(self) -> None:
        self.status = ApiStatus.DEPRECATED
        self.save(update_fields=["status", "updated_at"])


# ---------------------------------------------------------------------------
# ApiEndpoint
# ---------------------------------------------------------------------------


class ApiEndpoint(models.Model):
    """Individual REST endpoint within an ApiCatalog entry."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(ApiCatalog, on_delete=models.CASCADE, related_name="endpoints")
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=HttpMethod.choices)
    operation_id = models.CharField(max_length=100)
    summary = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    requires_auth = models.BooleanField(default=True)
    required_scopes = models.JSONField(default=list)
    is_deprecated = models.BooleanField(default=False)
    deprecated_at = models.DateTimeField(null=True, blank=True)
    request_schema = models.JSONField(null=True, blank=True)
    response_schema = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_api_endpoints"
        unique_together = [("catalog", "path", "method")]
        ordering = ["path", "method"]

    def __str__(self) -> str:
        return f"{self.method} {self.path}"


# ---------------------------------------------------------------------------
# ApiApplication
# ---------------------------------------------------------------------------


class ApiApplication(models.Model):
    """
    A registered API consumer application (internal service, partner, product).
    Owns ApiKeys and ApiSubscriptions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    classification = models.CharField(
        max_length=20, choices=ApiClassification.choices, default=ApiClassification.INTERNAL
    )
    status = models.CharField(max_length=20, choices=ApiStatus.choices, default=ApiStatus.ACTIVE)
    owner_user_id = models.CharField(max_length=255, blank=True)
    owner_email = models.EmailField(blank=True)
    callback_urls = models.JSONField(default=list)
    allowed_origins = models.JSONField(default=list)
    contact_email = models.EmailField(blank=True)
    is_trusted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_api_applications"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"App({self.slug})"

    def suspend(self) -> None:
        self.status = ApiStatus.SUSPENDED
        self.save(update_fields=["status", "updated_at"])

    def activate(self) -> None:
        self.status = ApiStatus.ACTIVE
        self.save(update_fields=["status", "updated_at"])


# ---------------------------------------------------------------------------
# ApiScope
# ---------------------------------------------------------------------------


class ApiScope(models.Model):
    """OAuth 2.1 scope definition for a specific API catalog."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(ApiCatalog, on_delete=models.CASCADE, related_name="scopes")
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    is_sensitive = models.BooleanField(default=False)
    requires_mfa = models.BooleanField(default=False)
    requires_consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_api_scopes"
        unique_together = [("catalog", "name")]

    def __str__(self) -> str:
        return f"Scope({self.name})"


# ---------------------------------------------------------------------------
# ApiKey
# ---------------------------------------------------------------------------


class ApiKey(models.Model):
    """
    API key for machine-to-machine authentication.
    Key is stored as SHA-256 hash; raw value shown once at creation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        ApiApplication, on_delete=models.CASCADE, related_name="api_keys"
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=200)
    key_prefix = models.CharField(max_length=12, unique=True)
    key_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20, choices=ApiKeyStatus.choices, default=ApiKeyStatus.ACTIVE
    )
    scopes = models.JSONField(default=list)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=255, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_api_keys"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ApiKey({self.key_prefix}..., {self.status})"

    @classmethod
    def generate(
        cls,
        application,
        name: str,
        scopes: list = None,
        tenant_id=None,
        created_by: str = "",
        expires_at=None,
    ):
        raw = f"ck_{secrets.token_urlsafe(32)}"
        prefix = raw[:12]
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        obj = cls.objects.create(
            application=application,
            tenant_id=tenant_id,
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            scopes=scopes or [],
            created_by=created_by,
            expires_at=expires_at,
        )
        return obj, raw

    def verify(self, raw_key: str) -> bool:
        return hashlib.sha256(raw_key.encode()).hexdigest() == self.key_hash

    def revoke(self, revoked_by: str = "") -> None:
        self.status = ApiKeyStatus.REVOKED
        self.revoked_at = timezone.now()
        self.revoked_by = revoked_by
        self.save(update_fields=["status", "revoked_at", "revoked_by"])

    @property
    def is_valid(self) -> bool:
        if self.status != ApiKeyStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


# ---------------------------------------------------------------------------
# ApiSubscription
# ---------------------------------------------------------------------------


class ApiSubscription(models.Model):
    """Links an ApiApplication to an ApiCatalog with approved scopes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        ApiApplication, on_delete=models.CASCADE, related_name="subscriptions"
    )
    catalog = models.ForeignKey(ApiCatalog, on_delete=models.CASCADE, related_name="subscriptions")
    approved_scopes = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=ApiStatus.choices, default=ApiStatus.ACTIVE)
    approved_by = models.CharField(max_length=255, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_api_subscriptions"
        unique_together = [("application", "catalog")]

    def __str__(self) -> str:
        return f"Sub({self.application.slug} -> {self.catalog.slug})"

    @property
    def is_active(self) -> bool:
        if self.status != ApiStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


# ---------------------------------------------------------------------------
# ApiRateLimit
# ---------------------------------------------------------------------------


class ApiRateLimit(models.Model):
    """Rate limit configuration per scope (tenant/user/app/global)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(
        ApiCatalog, on_delete=models.CASCADE, related_name="rate_limits", null=True, blank=True
    )
    application = models.ForeignKey(
        ApiApplication, on_delete=models.CASCADE, related_name="rate_limits", null=True, blank=True
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    scope = models.CharField(
        max_length=20, choices=RateLimitScope.choices, default=RateLimitScope.TENANT
    )
    requests_per_minute = models.PositiveIntegerField(default=60)
    requests_per_hour = models.PositiveIntegerField(default=3600)
    requests_per_day = models.PositiveIntegerField(default=86400)
    burst_size = models.PositiveIntegerField(default=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_api_rate_limits"

    def __str__(self) -> str:
        return f"RateLimit({self.scope}, {self.requests_per_minute}/min)"


# ---------------------------------------------------------------------------
# ApiConsumer
# ---------------------------------------------------------------------------


class ApiConsumer(models.Model):
    """Resolved consumer context from a request (tenant + application + user)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        ApiApplication, on_delete=models.SET_NULL, null=True, blank=True
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=255, blank=True)
    kong_consumer_id = models.CharField(max_length=255, blank=True, unique=True)
    rate_limit_tier = models.CharField(max_length=50, default="standard")
    is_trusted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_api_consumers"

    def __str__(self) -> str:
        return f"Consumer(app={self.application_id}, tenant={self.tenant_id})"


# ---------------------------------------------------------------------------
# ApiUsage
# ---------------------------------------------------------------------------


class ApiUsage(models.Model):
    """Per-request API usage record for billing and analytics."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(ApiCatalog, on_delete=models.SET_NULL, null=True, blank=True)
    application = models.ForeignKey(
        ApiApplication, on_delete=models.SET_NULL, null=True, blank=True
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=255, blank=True)
    endpoint_path = models.CharField(max_length=500)
    http_method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField()
    latency_ms = models.PositiveIntegerField(default=0)
    request_size_bytes = models.PositiveIntegerField(default=0)
    response_size_bytes = models.PositiveIntegerField(default=0)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)
    api_version = models.CharField(max_length=10, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    is_error = models.BooleanField(default=False, db_index=True)
    is_rate_limited = models.BooleanField(default=False)

    class Meta:
        db_table = "platform_api_usage"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant_id", "timestamp"]),
            models.Index(fields=["catalog_id", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"Usage({self.http_method} {self.endpoint_path}, {self.status_code})"


# ---------------------------------------------------------------------------
# ApiContract
# ---------------------------------------------------------------------------


class ApiContract(models.Model):
    """
    API contract definition for contract testing (ADR-0003 S7.3 Risk-1).
    Stores OpenAPI schema snapshot for backward-compat checking.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(ApiCatalog, on_delete=models.CASCADE, related_name="contracts")
    version = models.ForeignKey(ApiVersion, on_delete=models.PROTECT)
    consumer_name = models.CharField(max_length=200)
    schema_snapshot = models.JSONField(default=dict)
    schema_hash = models.CharField(max_length=64)
    is_valid = models.BooleanField(default=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    validation_errors = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_api_contracts"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Contract({self.catalog.slug}, {self.consumer_name})"

    def validate_against(self, current_schema: dict) -> bool:
        current_hash = hashlib.sha256(str(sorted(current_schema.items())).encode()).hexdigest()
        if current_hash != self.schema_hash:
            self.is_valid = False
            self.validation_errors = [{"error": "schema_drift", "message": "Schema hash mismatch"}]
        else:
            self.is_valid = True
            self.validation_errors = []
        self.last_validated_at = timezone.now()
        self.save(update_fields=["is_valid", "validation_errors", "last_validated_at"])
        return self.is_valid


# ---------------------------------------------------------------------------
# ApiPolicy
# ---------------------------------------------------------------------------


class ApiPolicy(models.Model):
    """Governance policy applied to an API catalog (auth, quota, CORS, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(ApiCatalog, on_delete=models.CASCADE, related_name="policies")
    name = models.CharField(max_length=100)
    policy_type = models.CharField(
        max_length=50,
        choices=[
            ("auth", "Authentication"),
            ("rate_limit", "Rate Limit"),
            ("cors", "CORS"),
            ("ip_allowlist", "IP Allowlist"),
            ("request_transform", "Request Transform"),
            ("response_transform", "Response Transform"),
            ("logging", "Logging"),
            ("caching", "Caching"),
        ],
    )
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    priority = models.PositiveSmallIntegerField(default=100)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_api_policies"
        ordering = ["priority", "name"]

    def __str__(self) -> str:
        return f"Policy({self.name}, {self.policy_type})"


# ---------------------------------------------------------------------------
# ApiWebhook
# ---------------------------------------------------------------------------


class ApiWebhook(models.Model):
    """
    Webhook subscription. Delivers events to external/internal endpoints.
    HMAC-SHA256 signature verifies authenticity.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        ApiApplication, on_delete=models.CASCADE, related_name="webhooks"
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=200)
    target_url = models.URLField()
    secret = models.CharField(max_length=64)
    events = models.JSONField(default=list)
    status = models.CharField(
        max_length=20, choices=WebhookStatus.choices, default=WebhookStatus.ACTIVE
    )
    max_retries = models.PositiveSmallIntegerField(default=3)
    retry_delay_seconds = models.PositiveIntegerField(default=60)
    headers = models.JSONField(default=dict)
    last_delivery_at = models.DateTimeField(null=True, blank=True)
    last_delivery_status = models.CharField(max_length=20, blank=True)
    failure_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_api_webhooks"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"Webhook({self.name}, {self.status})"

    @classmethod
    def create_with_secret(cls, **kwargs):
        kwargs["secret"] = secrets.token_hex(32)
        return cls.objects.create(**kwargs)

    def compute_signature(self, payload: str) -> str:
        import hmac

        return hmac.new(self.secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def pause(self) -> None:
        self.status = WebhookStatus.PAUSED
        self.save(update_fields=["status", "updated_at"])

    def disable(self) -> None:
        self.status = WebhookStatus.DISABLED
        self.save(update_fields=["status", "updated_at"])


# ---------------------------------------------------------------------------
# ApiWebhookDelivery
# ---------------------------------------------------------------------------


class ApiWebhookDelivery(models.Model):
    """Record of each webhook delivery attempt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(ApiWebhook, on_delete=models.CASCADE, related_name="deliveries")
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, choices=WebhookDeliveryStatus.choices, default=WebhookDeliveryStatus.PENDING
    )
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    response_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    signature = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_api_webhook_deliveries"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Delivery({self.event_type}, {self.status}, attempt={self.attempt_count})"

    def mark_delivered(self, response_code: int, response_body: str = "") -> None:
        self.status = WebhookDeliveryStatus.DELIVERED
        self.response_status_code = response_code
        self.response_body = response_body
        self.delivered_at = timezone.now()
        self.save(update_fields=["status", "response_status_code", "response_body", "delivered_at"])

    def mark_failed(self, error: str, response_code: int = None) -> None:
        self.attempt_count += 1
        self.error_message = error
        if response_code:
            self.response_status_code = response_code
        if self.attempt_count >= self.max_attempts:
            self.status = WebhookDeliveryStatus.DEAD
        else:
            self.status = WebhookDeliveryStatus.RETRYING
            from datetime import timedelta

            self.next_retry_at = timezone.now() + timedelta(
                seconds=self.webhook.retry_delay_seconds * self.attempt_count
            )
        self.save(
            update_fields=[
                "status",
                "attempt_count",
                "error_message",
                "response_status_code",
                "next_retry_at",
            ]
        )


# ---------------------------------------------------------------------------
# IdempotencyKey
# ---------------------------------------------------------------------------


class IdempotencyKey(models.Model):
    """
    Stores idempotency keys to prevent duplicate processing.
    ADR-0030 S3.1: safe retry without side effects.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=255, db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    application_id = models.UUIDField(null=True, blank=True)
    request_method = models.CharField(max_length=10)
    request_path = models.CharField(max_length=500)
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    processing = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "platform_idempotency_keys"
        unique_together = [("key", "tenant_id")]

    def __str__(self) -> str:
        return f"IdempotencyKey({self.key[:16]}..., {self.request_method} {self.request_path})"

    @property
    def is_expired(self) -> bool:
        return self.expires_at < timezone.now()

    def complete(self, response_status: int, response_body: str) -> None:
        self.response_status = response_status
        self.response_body = response_body
        self.processing = False
        self.save(update_fields=["response_status", "response_body", "processing"])
