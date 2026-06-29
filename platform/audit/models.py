"""
CyberCom Platform Audit & Compliance Framework — Domain Models.
ADR-0028: immutable, hash-chained, tamper-evident audit sink.
ADR-0002: multi-tenant. ADR-0005: identity integration.
"""

import hashlib
import uuid

from django.db import models
from django.utils import timezone

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    READ = "read", "Read"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    PERMISSION_DENIED = "permission_denied", "Permission Denied"
    BREAK_GLASS = "break_glass", "Break Glass"
    EXPORT = "export", "Data Export"
    IMPORT = "import", "Data Import"
    APPROVE = "approve", "Approve"
    REJECT = "reject", "Reject"
    SIGN = "sign", "Sign"
    VERIFY = "verify", "Verify"
    ARCHIVE = "archive", "Archive"
    PURGE = "purge", "Purge"


class AuditStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"
    DENIED = "denied", "Denied"


class AuditCategoryCode(models.TextChoices):
    AUTHENTICATION = "authentication", "Authentication"
    AUTHORIZATION = "authorization", "Authorization"
    CLINICAL = "clinical", "Clinical"
    FINANCIAL = "financial", "Financial"
    GOVERNMENT = "government", "Government"
    ADMINISTRATIVE = "administrative", "Administrative"
    SYSTEM = "system", "System"
    CONFIGURATION = "configuration", "Configuration"
    SECURITY = "security", "Security"
    AI = "ai", "AI / Machine Learning"
    ERP = "erp", "ERP / Business"
    IDENTITY = "identity", "Identity"


class DataClassification(models.TextChoices):
    PUBLIC = "public", "Public"
    INTERNAL = "internal", "Internal"
    CONFIDENTIAL = "confidential", "Confidential"
    RESTRICTED = "restricted", "Restricted"
    PHI = "phi", "Protected Health Information"
    PII = "pii", "Personally Identifiable Information"
    FINANCIAL = "financial", "Financial Data"
    GOVERNMENT_SENSITIVE = "government_sensitive", "Government Sensitive"


class ComplianceFrameworkCode(models.TextChoices):
    HIPAA = "hipaa", "HIPAA S164"
    GDPR = "gdpr", "GDPR"
    PDPL = "pdpl", "Saudi PDPL"
    UAE_DP = "uae_dp", "UAE Data Protection"
    JORDAN_DP = "jordan_dp", "Jordan Personal Data Protection"
    SOC2 = "soc2", "SOC 2 Type II"
    ISO27001 = "iso27001", "ISO 27001"
    NCA_ECC = "nca_ecc", "NCA ECC (Saudi)"
    HEALTHCARE_ACCREDITATION = "healthcare_accreditation", "Healthcare Accreditation (JCI/TJC)"
    PCI_DSS = "pci_dss", "PCI DSS"


class ComplianceRuleSeverity(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"
    INFORMATIONAL = "informational", "Informational"


class ViolationStatus(models.TextChoices):
    OPEN = "open", "Open"
    ACKNOWLEDGED = "acknowledged", "Acknowledged"
    REMEDIATED = "remediated", "Remediated"
    ACCEPTED_RISK = "accepted_risk", "Accepted Risk"
    FALSE_POSITIVE = "false_positive", "False Positive"


class LegalHoldStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    RELEASED = "released", "Released"
    EXPIRED = "expired", "Expired"


class ArchiveStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ARCHIVED = "archived", "Archived"
    VERIFIED = "verified", "Verified"
    FAILED = "failed", "Failed"


class AssessmentResult(models.TextChoices):
    PASSED = "passed", "Passed"
    FAILED = "failed", "Failed"
    PARTIAL = "partial", "Partial"
    PENDING = "pending", "Pending"


# ---------------------------------------------------------------------------
# AuditLog — base immutable record (backward compat, extended)
# ---------------------------------------------------------------------------


class AuditLog(models.Model):
    """
    Immutable platform audit log. Every sensitive operation emits one row.
    ADR-0028 S5: SHA-256 hash chain; no update/delete permitted.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=255, blank=True, db_index=True)
    session_id = models.CharField(max_length=255, blank=True)
    trace_id = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=30, choices=AuditAction.choices, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=AuditStatus.choices, default=AuditStatus.SUCCESS
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    entry_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "platform_audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant_id", "timestamp"]),
            models.Index(fields=["user_id", "timestamp"]),
            models.Index(fields=["action", "resource_type"]),
        ]

    def __str__(self) -> str:
        return f"AuditLog({self.action}, {self.resource_type}, {self.timestamp})"

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit log entries are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit log entries cannot be deleted.")

    def compute_hash(self) -> str:
        data = f"{self.id}{self.timestamp}{self.action}{self.resource_type}{self.resource_id}{self.previous_hash}"
        return hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# AuditCategory
# ---------------------------------------------------------------------------


class AuditCategory(models.Model):
    """Categorization metadata for audit event types."""

    code = models.CharField(max_length=50, choices=AuditCategoryCode.choices, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    data_classification = models.CharField(
        max_length=30, choices=DataClassification.choices, default=DataClassification.INTERNAL
    )
    retention_days_default = models.PositiveIntegerField(default=365)
    requires_purpose_of_use = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_audit_categories"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"AuditCategory({self.code})"


# ---------------------------------------------------------------------------
# AuditEvent — rich structured event (ADR-0028 S5.2 canonical schema)
# ---------------------------------------------------------------------------


class AuditEvent(models.Model):
    """
    Rich audit event conforming to ADR-0028 canonical schema.
    Written by all bounded contexts via AuditService. Immutable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    tenant_slug = models.CharField(max_length=100, blank=True, db_index=True)

    actor_user_id = models.CharField(max_length=255, blank=True, db_index=True)
    actor_username = models.CharField(max_length=255, blank=True)
    actor_role_claims = models.JSONField(default=list)
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    actor_device_id = models.CharField(max_length=200, blank=True)
    actor_session_id = models.CharField(max_length=200, blank=True)

    action = models.CharField(max_length=200, db_index=True)
    action_verb = models.CharField(max_length=30, choices=AuditAction.choices)
    category = models.CharField(
        max_length=50,
        choices=AuditCategoryCode.choices,
        default=AuditCategoryCode.SYSTEM,
        db_index=True,
    )
    data_classification = models.CharField(
        max_length=30, choices=DataClassification.choices, default=DataClassification.INTERNAL
    )

    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=255, blank=True, db_index=True)
    resource_uri = models.CharField(max_length=500, blank=True)

    # ADR-0028 S5.2: purpose_of_use mandatory for clinical category
    purpose_of_use = models.CharField(max_length=200, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)
    trace_id = models.CharField(max_length=64, blank=True)

    status = models.CharField(
        max_length=20, choices=AuditStatus.choices, default=AuditStatus.SUCCESS
    )
    outcome_description = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)

    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    previous_hash = models.CharField(max_length=64, blank=True)
    entry_hash = models.CharField(max_length=64, blank=True)
    chain_sequence = models.BigIntegerField(default=0)
    is_signed = models.BooleanField(default=False)

    class Meta:
        db_table = "platform_audit_events"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant_id", "timestamp"]),
            models.Index(fields=["actor_user_id", "timestamp"]),
            models.Index(fields=["category", "timestamp"]),
            models.Index(fields=["action", "resource_type"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self) -> str:
        return f"AuditEvent({self.action}, {self.tenant_slug}, {self.timestamp})"

    def save(self, *args, **kwargs):
        if self.pk and AuditEvent.objects.filter(pk=self.pk).exists():
            raise ValueError("AuditEvent records are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditEvent records cannot be deleted.")

    def compute_hash(self) -> str:
        data = (
            f"{self.id}{self.timestamp}{self.action}{self.resource_type}"
            f"{self.resource_id}{self.actor_user_id}{self.tenant_id}{self.previous_hash}"
        )
        return hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# AuditChain — tracks hash chain state per tenant per period
# ---------------------------------------------------------------------------


class AuditChain(models.Model):
    """
    Tracks the current chain tip for tamper-evident audit logs.
    ADR-0028 S5.1: SHA-256 block hash links each event to its predecessor.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    chain_key = models.CharField(max_length=100, unique=True)
    current_sequence = models.BigIntegerField(default=0)
    last_hash = models.CharField(max_length=64, blank=True)
    last_event_id = models.UUIDField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=True)
    verification_error = models.TextField(blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    total_events = models.BigIntegerField(default=0)

    class Meta:
        db_table = "platform_audit_chains"
        ordering = ["chain_key"]

    def __str__(self) -> str:
        return f"AuditChain({self.chain_key}, seq={self.current_sequence})"


# ---------------------------------------------------------------------------
# AuditRetentionPolicy
# ---------------------------------------------------------------------------


class AuditRetentionPolicy(models.Model):
    """Retention schedule for audit events by category and tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    category = models.CharField(max_length=50, choices=AuditCategoryCode.choices)
    data_classification = models.CharField(max_length=30, choices=DataClassification.choices)
    hot_retention_days = models.PositiveIntegerField(default=90)
    warm_retention_days = models.PositiveIntegerField(default=365)
    cold_retention_years = models.PositiveIntegerField(default=7)
    purge_after_cold = models.BooleanField(default=False)
    compliance_basis = models.CharField(
        max_length=30, choices=ComplianceFrameworkCode.choices, blank=True
    )
    legal_hold_override = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_audit_retention_policies"
        unique_together = [("tenant_id", "category", "data_classification")]

    def __str__(self) -> str:
        return f"RetentionPolicy({self.category}/{self.data_classification}, hot={self.hot_retention_days}d)"


# ---------------------------------------------------------------------------
# AuditArchive
# ---------------------------------------------------------------------------


class AuditArchive(models.Model):
    """Record of audit events archived to cold storage (WORM)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    archive_key = models.CharField(max_length=500, unique=True)
    category = models.CharField(max_length=50, choices=AuditCategoryCode.choices, blank=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    event_count = models.PositiveIntegerField(default=0)
    size_bytes = models.BigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    storage_backend = models.CharField(max_length=50, default="s3")
    storage_bucket = models.CharField(max_length=200, blank=True)
    storage_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=ArchiveStatus.choices, default=ArchiveStatus.PENDING
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_audit_archives"
        ordering = ["-period_end"]

    def __str__(self) -> str:
        return f"AuditArchive({self.archive_key}, {self.status})"


# ---------------------------------------------------------------------------
# AuditSignature
# ---------------------------------------------------------------------------


class AuditSignature(models.Model):
    """
    KMS/HSM digital signature for an audit chain block.
    ADR-0028 S5.1: periodic sealing with external KMS keys.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chain = models.ForeignKey(AuditChain, on_delete=models.PROTECT, related_name="signatures")
    signed_at = models.DateTimeField(default=timezone.now)
    sequence_from = models.BigIntegerField()
    sequence_to = models.BigIntegerField()
    block_hash = models.CharField(max_length=64)
    signature = models.TextField()
    kms_key_id = models.CharField(max_length=500, blank=True)
    algorithm = models.CharField(max_length=50, default="SHA256withRSA")
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform_audit_signatures"
        ordering = ["-signed_at"]

    def __str__(self) -> str:
        return f"AuditSignature(chain={self.chain.chain_key}, seq={self.sequence_from}-{self.sequence_to})"


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------


class AuditEntry(models.Model):
    """Enriched audit entry linking an AuditEvent to its chain position and category."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(AuditEvent, on_delete=models.PROTECT, related_name="entry")
    chain = models.ForeignKey(AuditChain, on_delete=models.PROTECT, related_name="entries")
    category_ref = models.ForeignKey(
        AuditCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="entries"
    )
    sequence = models.BigIntegerField(db_index=True)
    compliance_tags = models.JSONField(default=list)
    is_high_risk = models.BooleanField(default=False, db_index=True)
    risk_score = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_audit_entries"
        ordering = ["-sequence"]

    def __str__(self) -> str:
        return f"AuditEntry(seq={self.sequence}, chain={self.chain.chain_key})"


# ---------------------------------------------------------------------------
# AuditExport
# ---------------------------------------------------------------------------


class AuditExport(models.Model):
    """Record of audit log exports for compliance and investigation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    requested_by = models.CharField(max_length=255)
    reason = models.TextField()
    filter_criteria = models.JSONField(default=dict)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    event_count = models.PositiveIntegerField(default=0)
    format = models.CharField(
        max_length=20,
        default="json",
        choices=[
            ("json", "JSON"),
            ("csv", "CSV"),
            ("ndjson", "NDJSON"),
            ("parquet", "Parquet"),
        ],
    )
    download_url = models.URLField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("ready", "Ready"),
            ("failed", "Failed"),
            ("expired", "Expired"),
        ],
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform_audit_exports"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AuditExport({self.id}, {self.status})"


# ---------------------------------------------------------------------------
# LegalHold
# ---------------------------------------------------------------------------


class LegalHold(models.Model):
    """Legal hold: preserves records from deletion for litigation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=300)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=LegalHoldStatus.choices, default=LegalHoldStatus.ACTIVE
    )
    case_reference = models.CharField(max_length=200, blank=True)
    custodians = models.JSONField(default=list)
    resource_types = models.JSONField(default=list)
    resource_ids = models.JSONField(default=list)
    scope_query = models.JSONField(default=dict, blank=True)
    scope_description = models.TextField(blank=True)
    created_by = models.CharField(max_length=255)
    activated_at = models.DateTimeField(default=timezone.now)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.CharField(max_length=255, blank=True)
    release_reason = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_legal_holds"
        ordering = ["-activated_at"]

    def __str__(self) -> str:
        return f"LegalHold({self.name}, {self.status})"

    def release(self, released_by: str, reason: str) -> None:
        if self.status != LegalHoldStatus.ACTIVE:
            raise ValueError(f"Cannot release legal hold in status {self.status}")
        self.status = LegalHoldStatus.RELEASED
        self.released_at = timezone.now()
        self.released_by = released_by
        self.release_reason = reason
        self.save(
            update_fields=["status", "released_at", "released_by", "release_reason", "updated_at"]
        )

    @property
    def is_active(self) -> bool:
        if self.status != LegalHoldStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


# ---------------------------------------------------------------------------
# ComplianceProfile
# ---------------------------------------------------------------------------


class ComplianceProfile(models.Model):
    """Compliance framework configuration for a tenant or platform-wide."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    framework = models.CharField(max_length=30, choices=ComplianceFrameworkCode.choices)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=False)
    passing_score = models.PositiveSmallIntegerField(default=80)
    description = models.TextField(blank=True)
    applicable_categories = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_compliance_profiles"
        unique_together = [("tenant_id", "framework")]
        ordering = ["framework"]

    def __str__(self) -> str:
        return f"ComplianceProfile({self.framework}, v{self.version})"


# ---------------------------------------------------------------------------
# ComplianceRule
# ---------------------------------------------------------------------------


class ComplianceRule(models.Model):
    """A single testable compliance control within a ComplianceProfile."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(ComplianceProfile, on_delete=models.CASCADE, related_name="rules")
    rule_id = models.CharField(max_length=50)
    name = models.CharField(max_length=300)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=ComplianceRuleSeverity.choices)
    category = models.CharField(max_length=50, choices=AuditCategoryCode.choices, blank=True)
    check_type = models.CharField(
        max_length=50,
        default="manual",
        choices=[
            ("manual", "Manual"),
            ("automated", "Automated"),
            ("hybrid", "Hybrid"),
        ],
    )
    check_query = models.TextField(blank=True)
    remediation_guidance = models.TextField(blank=True)
    reference = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    weight = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_compliance_rules"
        unique_together = [("profile", "rule_id")]
        ordering = ["-severity", "rule_id"]

    def __str__(self) -> str:
        return f"ComplianceRule({self.profile.framework}/{self.rule_id}: {self.severity})"


# ---------------------------------------------------------------------------
# ComplianceViolation
# ---------------------------------------------------------------------------


class ComplianceViolation(models.Model):
    """A detected violation of a compliance rule."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(ComplianceRule, on_delete=models.CASCADE, related_name="violations")
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=ViolationStatus.choices, default=ViolationStatus.OPEN
    )
    detected_at = models.DateTimeField(default=timezone.now)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    evidence = models.JSONField(default=dict, blank=True)
    remediation_notes = models.TextField(blank=True)
    remediated_at = models.DateTimeField(null=True, blank=True)
    remediated_by = models.CharField(max_length=255, blank=True)
    accepted_by = models.CharField(max_length=255, blank=True)
    accepted_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_compliance_violations"
        ordering = ["-detected_at"]

    def __str__(self) -> str:
        return f"Violation({self.rule.rule_id}, {self.status})"

    def remediate(self, by: str, notes: str = "") -> None:
        self.status = ViolationStatus.REMEDIATED
        self.remediated_at = timezone.now()
        self.remediated_by = by
        self.remediation_notes = notes
        self.save(
            update_fields=[
                "status",
                "remediated_at",
                "remediated_by",
                "remediation_notes",
                "updated_at",
            ]
        )

    def accept_risk(self, by: str, reason: str) -> None:
        self.status = ViolationStatus.ACCEPTED_RISK
        self.accepted_by = by
        self.accepted_reason = reason
        self.save(update_fields=["status", "accepted_by", "accepted_reason", "updated_at"])


# ---------------------------------------------------------------------------
# ComplianceAssessment
# ---------------------------------------------------------------------------


class ComplianceAssessment(models.Model):
    """Periodic compliance assessment run against a ComplianceProfile."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        ComplianceProfile, on_delete=models.CASCADE, related_name="assessments"
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    assessed_at = models.DateTimeField(default=timezone.now)
    assessed_by = models.CharField(max_length=255, blank=True, default="system")
    result = models.CharField(
        max_length=20, choices=AssessmentResult.choices, default=AssessmentResult.PENDING
    )
    total_rules = models.PositiveIntegerField(default=0)
    passed_rules = models.PositiveIntegerField(default=0)
    failed_rules = models.PositiveIntegerField(default=0)
    score = models.PositiveSmallIntegerField(default=0)
    critical_violations = models.PositiveIntegerField(default=0)
    high_violations = models.PositiveIntegerField(default=0)
    rule_results = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_compliance_assessments"
        ordering = ["-assessed_at"]

    def __str__(self) -> str:
        return f"Assessment({self.profile.framework}, score={self.score}, {self.result})"

    @property
    def passed(self) -> bool:
        return self.score >= self.profile.passing_score


# ---------------------------------------------------------------------------
# ComplianceReport
# ---------------------------------------------------------------------------


class ComplianceReport(models.Model):
    """Generated compliance report for a period."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    title = models.CharField(max_length=300)
    framework = models.CharField(max_length=30, choices=ComplianceFrameworkCode.choices)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    generated_by = models.CharField(max_length=255, default="system")
    generated_at = models.DateTimeField(default=timezone.now)
    summary = models.TextField(blank=True)
    overall_score = models.PositiveSmallIntegerField(default=0)
    overall_result = models.CharField(
        max_length=20, choices=AssessmentResult.choices, default=AssessmentResult.PENDING
    )
    total_controls = models.PositiveIntegerField(default=0)
    passing_controls = models.PositiveIntegerField(default=0)
    open_violations = models.PositiveIntegerField(default=0)
    findings = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    report_data = models.JSONField(default=dict)
    download_url = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "platform_compliance_reports"
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"ComplianceReport({self.framework}, {self.period_start:%Y-%m-%d})"


# ---------------------------------------------------------------------------
# EvidenceRecord
# ---------------------------------------------------------------------------


class EvidenceRecord(models.Model):
    """A single piece of evidence for compliance or legal proceedings."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    evidence_type = models.CharField(
        max_length=50,
        choices=[
            ("audit_log", "Audit Log"),
            ("screenshot", "Screenshot"),
            ("document", "Document"),
            ("export", "Data Export"),
            ("attestation", "Attestation"),
            ("system_config", "System Configuration"),
        ],
    )
    source_system = models.CharField(max_length=100, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)
    content = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_hash_sha256 = models.CharField(max_length=64, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    collected_at = models.DateTimeField(default=timezone.now)
    collected_by = models.CharField(max_length=255, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    chain_of_custody = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_evidence_records"
        ordering = ["-collected_at"]

    def __str__(self) -> str:
        return f"Evidence({self.title}, {self.evidence_type})"

    def lock(self) -> None:
        self.is_locked = True
        self.locked_at = timezone.now()
        self.save(update_fields=["is_locked", "locked_at", "updated_at"])


# ---------------------------------------------------------------------------
# EvidencePackage
# ---------------------------------------------------------------------------


class EvidencePackage(models.Model):
    """Bundle of EvidenceRecords for a legal case or compliance audit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    purpose = models.CharField(
        max_length=50,
        choices=[
            ("legal_proceeding", "Legal Proceeding"),
            ("regulatory_audit", "Regulatory Audit"),
            ("internal_investigation", "Internal Investigation"),
            ("compliance_certification", "Compliance Certification"),
        ],
    )
    case_reference = models.CharField(max_length=200, blank=True)
    records = models.ManyToManyField(EvidenceRecord, blank=True, related_name="packages")
    legal_hold = models.ForeignKey(
        LegalHold,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_packages",
    )
    created_by = models.CharField(max_length=255)
    sealed_at = models.DateTimeField(null=True, blank=True)
    sealed_by = models.CharField(max_length=255, blank=True)
    package_hash = models.CharField(max_length=64, blank=True)
    download_url = models.URLField(blank=True)
    is_sealed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_evidence_packages"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"EvidencePackage({self.name}, {self.purpose})"

    def seal(self, sealed_by: str) -> None:
        if self.is_sealed:
            raise ValueError("Package already sealed.")
        self.is_sealed = True
        self.sealed_at = timezone.now()
        self.sealed_by = sealed_by
        record_ids = list(self.records.values_list("id", flat=True))
        self.package_hash = hashlib.sha256(
            str(sorted([str(r) for r in record_ids])).encode()
        ).hexdigest()
        self.save(
            update_fields=["is_sealed", "sealed_at", "sealed_by", "package_hash", "updated_at"]
        )
        self.records.all().update(is_locked=True)
