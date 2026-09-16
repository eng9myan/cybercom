"""
Security domain: multi-factor authentication, step-up authorisation,
brute-force lockout, and an append-only security audit log.

The ST4S assessment rejected CyEd for having no second factor anywhere. This
app supplies it as first-class, tenant-scoped data:

  MfaEnrollment   one per user per tenant; holds the TOTP shared secret
                  (encrypted at rest via core.crypto) and the replay watermark.
  MfaBackupCode   ten single-use recovery codes per enrolment, stored only as
                  salted PBKDF2 hashes.
  MfaSession      proof that a user completed MFA recently — the anchor for
                  step-up authorisation on sensitive operations.
  LoginAttempt    every MFA attempt, success or failure, for lockout accounting.
  SecurityEvent   append-only audit trail. Never contains a secret or a code.
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone

from core.crypto import EncryptedTextField
from platform.common.models import BaseModel


def normalize_email(value) -> str:
    return str(value or "").strip().lower()


class MfaEnrollment(BaseModel):
    """
    A user's TOTP authenticator binding.

    `confirmed` separates "secret issued, app not yet proven" from "second
    factor live". An unconfirmed enrolment grants nothing. `last_used_counter`
    is the RFC 6238 §5.2 replay watermark: a time step is accepted at most once.
    """

    user_email = models.CharField(max_length=255)
    # Encrypted at rest. Never serialized — see serializers.MfaEnrollmentSerializer.
    secret = EncryptedTextField()
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_counter = models.BigIntegerField(default=0)
    # Most recent successful factor check — drives the step-up window.
    last_verified_at = models.DateTimeField(null=True, blank=True)
    label = models.CharField(max_length=100, blank=True)  # e.g. "iPhone 15"

    class Meta:
        db_table = "cyed_mfa_enrollments"
        ordering = ["user_email", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "user_email"], name="uniq_mfa_enrollment_per_user"
            )
        ]
        indexes = [models.Index(fields=["tenant_id", "user_email"], name="idx_mfa_enrol_tenant_user")]

    def save(self, *args, **kwargs):
        self.user_email = normalize_email(self.user_email)
        super().save(*args, **kwargs)

    @property
    def unused_backup_code_count(self) -> int:
        return self.backup_codes.filter(used_at__isnull=True).count()

    def __str__(self):
        # Deliberately excludes the secret: __str__ ends up in logs.
        return f"MFA {self.user_email} ({'confirmed' if self.confirmed else 'pending'})"


class MfaBackupCode(BaseModel):
    """A single-use recovery code. Only a salted hash is ever persisted."""

    enrollment = models.ForeignKey(
        MfaEnrollment, on_delete=models.CASCADE, related_name="backup_codes"
    )
    salt = models.CharField(max_length=64)
    code_hash = models.CharField(max_length=128)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_mfa_backup_codes"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["enrollment", "used_at"], name="idx_mfa_backup_unused")]

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def __str__(self):
        return f"Backup code for {self.enrollment_id} ({'used' if self.is_used else 'unused'})"


class MfaSession(BaseModel):
    """
    Evidence of a recent successful MFA check.

    Sensitive operations (payroll runs, bulk exports, permission changes) can
    require one of these via `stepup.RequiresRecentMfa` instead of trusting a
    long-lived bearer token.
    """

    METHODS = [("totp", "Authenticator app (TOTP)"), ("backup", "Backup code")]

    user_email = models.CharField(max_length=255)
    method = models.CharField(max_length=20, choices=METHODS, default="totp")
    verified_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip = models.CharField(max_length=45, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_mfa_sessions"
        ordering = ["-verified_at"]
        indexes = [models.Index(fields=["tenant_id", "user_email"], name="idx_mfa_sess_tenant_user")]

    def save(self, *args, **kwargs):
        self.user_email = normalize_email(self.user_email)
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        now = timezone.now()
        return self.revoked_at is None and self.expires_at > now

    def revoke(self):
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at", "updated_at"])

    def __str__(self):
        return f"MFA session {self.user_email} until {self.expires_at:%Y-%m-%d %H:%M}"


class LoginAttempt(BaseModel):
    """
    One authentication/MFA attempt. The throttle counts the failures here; the
    row also gives incident response a per-IP trail. No code is ever recorded.
    """

    PURPOSES = [
        ("mfa", "MFA challenge"),
        ("login", "Password login"),
        ("step_up", "Step-up authorisation"),
    ]

    identifier = models.CharField(max_length=255)  # normalised email
    purpose = models.CharField(max_length=20, choices=PURPOSES, default="mfa")
    ip = models.CharField(max_length=45, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    succeeded = models.BooleanField(default=False)
    reason = models.CharField(max_length=60, blank=True)  # e.g. "invalid_code"

    class Meta:
        db_table = "cyed_login_attempts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "identifier", "purpose"], name="idx_login_att_ident"),
            models.Index(fields=["tenant_id", "created_at"], name="idx_login_att_created"),
        ]

    def save(self, *args, **kwargs):
        self.identifier = normalize_email(self.identifier)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.identifier} {self.purpose} {'ok' if self.succeeded else 'fail'}"


class SecurityEvent(BaseModel):
    """
    Append-only security audit trail. Rows cannot be edited or deleted through
    the ORM instance API, and the API exposes list/retrieve only.

    `detail` is a short human string. Writing a secret, a TOTP code or a backup
    code into it is a defect — see test_no_secret_material_in_audit_trail.
    """

    MFA_ENROLLED = "mfa_enrolled"
    MFA_CONFIRMED = "mfa_confirmed"
    MFA_VERIFIED = "mfa_verified"
    MFA_FAILED = "mfa_failed"
    MFA_DISABLED = "mfa_disabled"
    MFA_BACKUP_USED = "mfa_backup_used"
    MFA_BACKUP_REGENERATED = "mfa_backup_regenerated"
    LOCKOUT = "lockout"
    STEP_UP_GRANTED = "step_up_granted"
    STEP_UP_DENIED = "step_up_denied"

    EVENT_TYPES = [
        (MFA_ENROLLED, "MFA enrolment started"),
        (MFA_CONFIRMED, "MFA enrolment confirmed"),
        (MFA_VERIFIED, "MFA verified"),
        (MFA_FAILED, "MFA verification failed"),
        (MFA_DISABLED, "MFA disabled"),
        (MFA_BACKUP_USED, "Backup code used"),
        (MFA_BACKUP_REGENERATED, "Backup codes regenerated"),
        (LOCKOUT, "Account locked (too many failures)"),
        (STEP_UP_GRANTED, "Step-up authorisation granted"),
        (STEP_UP_DENIED, "Step-up authorisation denied"),
    ]

    SEVERITIES = [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]

    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITIES, default="info")
    actor_email = models.CharField(max_length=255, blank=True)
    actor_roles = models.CharField(max_length=255, blank=True)
    ip = models.CharField(max_length=45, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    detail = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_security_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "event_type"], name="idx_sec_event_type"),
            models.Index(fields=["tenant_id", "actor_email"], name="idx_sec_event_actor"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("SecurityEvent rows are append-only and cannot be modified.")
        self.actor_email = normalize_email(self.actor_email)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("SecurityEvent rows are append-only and cannot be deleted.")

    def __str__(self):
        return f"[{self.severity}] {self.event_type} {self.actor_email}"


def default_expiry(minutes: int) -> timezone.datetime:
    return timezone.now() + timedelta(minutes=minutes)
