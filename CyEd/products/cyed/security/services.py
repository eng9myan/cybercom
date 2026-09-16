"""
MFA services: enrolment, verification, backup codes, lockout, and step-up.

Design rules that the tests enforce:
  * A secret leaves the server exactly once — at enrolment, before confirmation.
  * Backup codes leave the server exactly once — at generation. Only salted
    PBKDF2 hashes are stored, and every comparison is constant-time.
  * A TOTP time step is accepted at most once (replay watermark).
  * Repeated failures lock the identifier; the lock is recorded, not silent.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.utils import timezone

from products.cyed.security import totp as totp_lib
from products.cyed.security.models import (
    LoginAttempt, MfaBackupCode, MfaEnrollment, MfaSession, SecurityEvent, normalize_email,
)

BACKUP_CODE_COUNT = 10
BACKUP_CODE_BYTES = 5  # 10 hex chars — enough entropy, still typable
PBKDF2_ROUNDS = 200_000

# Lockout policy.
MAX_FAILURES = 5
FAILURE_WINDOW_MINUTES = 15
LOCKOUT_MINUTES = 15

# How long a successful factor check authorises sensitive work.
STEP_UP_MINUTES = 15


class MfaError(Exception):
    """Workflow violation (wrong state, bad code, already enrolled)."""


class MfaLockedOut(MfaError):
    """Too many recent failures for this identifier."""


# ── Backup codes ─────────────────────────────────────────────────────────────
def _hash_code(code: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", code.encode(), salt.encode(), PBKDF2_ROUNDS
    ).hex()


def generate_backup_codes(enrollment) -> list[str]:
    """
    Replace this enrolment's codes and return the plaintext ONCE.

    The caller must surface them to the user immediately; they are
    unrecoverable afterwards, which is the point.
    """
    enrollment.backup_codes.all().delete()
    plain = []
    for _ in range(BACKUP_CODE_COUNT):
        code = secrets.token_hex(BACKUP_CODE_BYTES)
        salt = secrets.token_hex(16)
        MfaBackupCode.objects.create(
            tenant_id=enrollment.tenant_id, enrollment=enrollment,
            salt=salt, code_hash=_hash_code(code, salt),
        )
        plain.append(code)
    return plain


def _consume_backup_code(enrollment, code: str) -> bool:
    """Constant-time check against every unused code; burns it on success."""
    supplied = (code or "").strip().lower().replace(" ", "").replace("-", "")
    matched = None
    for candidate in enrollment.backup_codes.filter(used_at__isnull=True):
        if hmac.compare_digest(_hash_code(supplied, candidate.salt), candidate.code_hash):
            matched = candidate
            # No early break: keep the work constant regardless of position.
    if matched is None:
        return False
    matched.used_at = timezone.now()
    matched.save(update_fields=["used_at", "updated_at"])
    return True


# ── Audit + lockout ──────────────────────────────────────────────────────────
def record_event(tenant_id, event_type, *, actor="", roles="", detail="", ip="",
                 user_agent="", severity="info"):
    return SecurityEvent.objects.create(
        tenant_id=tenant_id, event_type=event_type, severity=severity,
        actor_email=actor, actor_roles=roles, detail=detail[:255],
        ip=ip[:45], user_agent=user_agent[:255],
    )


def recent_failures(tenant_id, identifier, purpose="mfa"):
    since = timezone.now() - timedelta(minutes=FAILURE_WINDOW_MINUTES)
    return LoginAttempt.objects.filter(
        tenant_id=tenant_id, identifier=normalize_email(identifier),
        purpose=purpose, succeeded=False, created_at__gte=since,
    ).count()


def is_locked_out(tenant_id, identifier, purpose="mfa") -> bool:
    """
    Locked while the most recent failure is inside the cooldown AND the failure
    count is at the threshold. A success clears the streak (see record_attempt).
    """
    if recent_failures(tenant_id, identifier, purpose) < MAX_FAILURES:
        return False
    last = LoginAttempt.objects.filter(
        tenant_id=tenant_id, identifier=normalize_email(identifier), purpose=purpose,
    ).order_by("-created_at").first()
    if last is None:
        return False
    return last.created_at > timezone.now() - timedelta(minutes=LOCKOUT_MINUTES)


def record_attempt(tenant_id, identifier, *, succeeded, purpose="mfa", ip="",
                   user_agent="", reason=""):
    attempt = LoginAttempt.objects.create(
        tenant_id=tenant_id, identifier=identifier, purpose=purpose,
        succeeded=succeeded, ip=ip[:45], user_agent=user_agent[:255], reason=reason[:60],
    )
    if succeeded:
        # Clear the streak so a legitimate user is not locked out by old noise.
        LoginAttempt.objects.filter(
            tenant_id=tenant_id, identifier=normalize_email(identifier),
            purpose=purpose, succeeded=False,
        ).delete()
    return attempt


# ── Enrolment ────────────────────────────────────────────────────────────────
def start_enrollment(tenant_id, email, *, label="", issuer="CyEd"):
    """
    Issue a secret. Returns (enrollment, secret, otpauth_uri).

    Re-enrolling while unconfirmed simply rotates the secret — a user who lost
    the QR code before scanning it should not be stuck.
    """
    email = normalize_email(email)
    existing = MfaEnrollment.objects.filter(tenant_id=tenant_id, user_email=email).first()
    if existing and existing.confirmed:
        raise MfaError("MFA is already active for this account. Disable it first to re-enrol.")

    secret = totp_lib.generate_secret()
    if existing:
        existing.secret = secret
        existing.label = label or existing.label
        existing.save()
        enrollment = existing
    else:
        enrollment = MfaEnrollment.objects.create(
            tenant_id=tenant_id, user_email=email, secret=secret, label=label,
        )
    return enrollment, secret, totp_lib.provisioning_uri(secret, account=email, issuer=issuer)


def confirm_enrollment(tenant_id, email, code, *, ip="", user_agent=""):
    """Prove the authenticator works, activate it, and issue backup codes."""
    email = normalize_email(email)
    if is_locked_out(tenant_id, email):
        raise MfaLockedOut("Too many failed attempts. Try again shortly.")

    enrollment = MfaEnrollment.objects.filter(tenant_id=tenant_id, user_email=email).first()
    if enrollment is None:
        raise MfaError("Start enrolment before confirming it.")
    if enrollment.confirmed:
        raise MfaError("This enrolment is already confirmed.")

    counter = totp_lib.verify(enrollment.secret, code, after_counter=enrollment.last_used_counter)
    if counter is None:
        record_attempt(tenant_id, email, succeeded=False, ip=ip, user_agent=user_agent,
                       reason="invalid_code")
        record_event(tenant_id, SecurityEvent.MFA_FAILED, actor=email, ip=ip,
                     user_agent=user_agent, detail="Confirmation code rejected", severity="warning")
        raise MfaError("That code is not valid.")

    now = timezone.now()
    enrollment.confirmed = True
    enrollment.confirmed_at = now
    enrollment.last_used_counter = counter
    enrollment.last_used_at = now
    enrollment.last_verified_at = now
    enrollment.save()

    codes = generate_backup_codes(enrollment)
    # Confirming is itself a successful factor check, so it opens the step-up
    # window. Without this a user who just proved possession would immediately
    # be challenged again for a sensitive action — friction with no security
    # benefit, and the kind of thing that pushes people to disable MFA.
    MfaSession.objects.create(
        tenant_id=tenant_id, user_email=email, method="totp",
        expires_at=now + timedelta(minutes=STEP_UP_MINUTES),
        ip=ip[:45], user_agent=user_agent[:255],
    )
    record_attempt(tenant_id, email, succeeded=True, ip=ip, user_agent=user_agent)
    record_event(tenant_id, SecurityEvent.MFA_CONFIRMED, actor=email, ip=ip, user_agent=user_agent,
                 detail="Authenticator confirmed; backup codes issued")
    return enrollment, codes


def verify_code(tenant_id, email, code, *, ip="", user_agent="", create_session=True):
    """
    Check a TOTP code or a backup code. Returns (enrollment, method, session).

    A used time step is rejected, so a code observed over someone's shoulder is
    worthless within its own window.
    """
    email = normalize_email(email)
    if is_locked_out(tenant_id, email):
        record_event(tenant_id, SecurityEvent.LOCKOUT, actor=email, ip=ip, user_agent=user_agent,
                     detail="Verification attempted while locked out", severity="critical")
        raise MfaLockedOut("Too many failed attempts. Try again shortly.")

    enrollment = MfaEnrollment.objects.filter(
        tenant_id=tenant_id, user_email=email, confirmed=True
    ).first()
    if enrollment is None:
        raise MfaError("No confirmed MFA enrolment for this account.")

    method = None
    counter = totp_lib.verify(enrollment.secret, code, after_counter=enrollment.last_used_counter)
    if counter is not None:
        method = "totp"
        enrollment.last_used_counter = counter
    elif _consume_backup_code(enrollment, code):
        method = "backup"
        record_event(tenant_id, SecurityEvent.MFA_BACKUP_USED, actor=email, ip=ip,
                     user_agent=user_agent,
                     detail=f"{enrollment.unused_backup_code_count} backup code(s) remaining",
                     severity="warning")

    if method is None:
        record_attempt(tenant_id, email, succeeded=False, ip=ip, user_agent=user_agent,
                       reason="invalid_code")
        failures = recent_failures(tenant_id, email)
        record_event(tenant_id, SecurityEvent.MFA_FAILED, actor=email, ip=ip,
                     user_agent=user_agent, detail=f"Failure {failures}/{MAX_FAILURES}",
                     severity="warning")
        if failures >= MAX_FAILURES:
            record_event(tenant_id, SecurityEvent.LOCKOUT, actor=email, ip=ip,
                         user_agent=user_agent,
                         detail=f"Locked for {LOCKOUT_MINUTES} minutes", severity="critical")
        raise MfaError("That code is not valid.")

    now = timezone.now()
    enrollment.last_used_at = now
    enrollment.last_verified_at = now
    enrollment.save()
    record_attempt(tenant_id, email, succeeded=True, ip=ip, user_agent=user_agent)
    record_event(tenant_id, SecurityEvent.MFA_VERIFIED, actor=email, ip=ip, user_agent=user_agent,
                 detail=f"Verified via {method}")

    session = None
    if create_session:
        session = MfaSession.objects.create(
            tenant_id=tenant_id, user_email=email, method=method,
            expires_at=now + timedelta(minutes=STEP_UP_MINUTES),
            ip=ip[:45], user_agent=user_agent[:255],
        )
    return enrollment, method, session


def disable(tenant_id, email, code, *, ip="", user_agent=""):
    """
    Turn MFA off — but only for someone who can still pass it. Otherwise a
    stolen bearer token would be enough to strip the second factor.
    """
    email = normalize_email(email)
    enrollment = MfaEnrollment.objects.filter(
        tenant_id=tenant_id, user_email=email, confirmed=True
    ).first()
    if enrollment is None:
        raise MfaError("No confirmed MFA enrolment for this account.")

    verify_code(tenant_id, email, code, ip=ip, user_agent=user_agent, create_session=False)
    MfaSession.objects.filter(tenant_id=tenant_id, user_email=email, revoked_at__isnull=True) \
        .update(revoked_at=timezone.now())
    enrollment.delete()
    record_event(tenant_id, SecurityEvent.MFA_DISABLED, actor=email, ip=ip, user_agent=user_agent,
                 detail="MFA disabled by the account holder", severity="warning")
    return True


def has_recent_mfa(tenant_id, email, *, minutes=STEP_UP_MINUTES) -> bool:
    """True when this user completed a factor check inside the step-up window."""
    email = normalize_email(email)
    cutoff = timezone.now() - timedelta(minutes=minutes)
    return MfaSession.objects.filter(
        tenant_id=tenant_id, user_email=email, revoked_at__isnull=True,
        verified_at__gte=cutoff, expires_at__gt=timezone.now(),
    ).exists()


def status_for(tenant_id, email) -> dict:
    email = normalize_email(email)
    enrollment = MfaEnrollment.objects.filter(tenant_id=tenant_id, user_email=email).first()
    if enrollment is None:
        return {"enrolled": False, "confirmed": False, "backup_codes_remaining": 0,
                "step_up_active": False, "locked_out": is_locked_out(tenant_id, email)}
    return {
        "enrolled": True,
        "confirmed": enrollment.confirmed,
        "label": enrollment.label,
        "confirmed_at": enrollment.confirmed_at,
        "last_verified_at": enrollment.last_verified_at,
        "backup_codes_remaining": enrollment.unused_backup_code_count,
        "step_up_active": has_recent_mfa(tenant_id, email),
        "locked_out": is_locked_out(tenant_id, email),
    }
