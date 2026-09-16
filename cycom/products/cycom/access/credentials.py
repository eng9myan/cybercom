"""Manager PIN / barcode credentials for at-terminal approval (audit HR-4
follow-up, retail till workflow). A cashier signed in under their own limited
token can get a manager's value-based approval (pos_discount, pos_refund, …)
right at the till, without a full login/device handoff to the manager.

This is a net-new, deliberately narrow mechanism — nothing else in the
codebase does non-JWT, credential-based identity, and it should stay that way
outside this specific till workflow. It is an ADDITIONAL path alongside
`access.approvals.require_approval_authority`, never a replacement: a caller
who already holds the required role via their own token doesn't need a PIN at
all — see pos.views for the try-authority-then-try-credential pattern.

PINs/barcodes are never stored in plaintext — hashed with Django's own
password hasher, exactly like a user password. Verification is rate-limited
per tenant+scope to blunt brute-forcing an unattended terminal.
"""

from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from rest_framework.exceptions import PermissionDenied, ValidationError

from products.cycom.access.approvals import _slug, required_approver_role
from products.cycom.access.models import ManagerCredential

RATE_LIMIT_WINDOW_SECONDS = 300
RATE_LIMIT_MAX_ATTEMPTS = 5


def set_manager_pin(role_assignment, pin):
    if not pin or len(str(pin)) < 4:
        raise ValidationError("PIN must be at least 4 characters.")
    cred, _ = ManagerCredential.objects.get_or_create(
        tenant_id=role_assignment.tenant_id, role_assignment=role_assignment,
    )
    cred.pin_hash = make_password(str(pin))
    cred.is_active = True
    cred.save(update_fields=["pin_hash", "is_active"])
    return cred


def set_manager_barcode(role_assignment, barcode):
    if not barcode:
        raise ValidationError("barcode is required.")
    cred, _ = ManagerCredential.objects.get_or_create(
        tenant_id=role_assignment.tenant_id, role_assignment=role_assignment,
    )
    cred.barcode_hash = make_password(str(barcode))
    cred.is_active = True
    cred.save(update_fields=["barcode_hash", "is_active"])
    return cred


def _rate_limit_key(tenant_id, scope):
    return f"mgr-credential-attempts:{tenant_id}:{scope}"


def _assert_not_rate_limited(tenant_id, scope):
    key = _rate_limit_key(tenant_id, scope)
    if cache.get(key, 0) >= RATE_LIMIT_MAX_ATTEMPTS:
        raise PermissionDenied(
            "Too many manager-credential attempts — try again in a few minutes."
        )
    return key


def _record_failed_attempt(key):
    cache.set(key, cache.get(key, 0) + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)


def verify_manager_credential(tenant_id, document_type, amount, *, pin=None, barcode=None):
    """Returns the verified manager's `user_id` if `pin` or `barcode` matches
    an active credential for a role that satisfies `document_type`'s tier at
    `amount` (or an admin role's credential). Returns None on no match or no
    code supplied — never raises for a bad code, only for being rate-limited.
    """
    if not pin and not barcode:
        return None

    role_name = required_approver_role(tenant_id, document_type, amount)
    # No policy at all => the credential shortcut doesn't apply either; the
    # caller falls back to admin-required, same as require_approval_authority.
    if role_name is None:
        return None

    scope = f"{document_type}:{'pin' if pin else 'barcode'}"
    rl_key = _assert_not_rate_limited(tenant_id, scope)

    target_slug = _slug(role_name)
    from products.cycom.access.approvals import ADMIN_ROLES

    candidates = ManagerCredential.objects.filter(
        tenant_id=tenant_id, is_active=True,
    ).select_related("role_assignment__role")
    if pin:
        candidates = candidates.exclude(pin_hash="")
    else:
        candidates = candidates.exclude(barcode_hash="")

    for cred in candidates:
        role_slug = _slug(cred.role_assignment.role.name)
        if role_slug != target_slug and role_slug not in ADMIN_ROLES:
            continue
        hashed = cred.pin_hash if pin else cred.barcode_hash
        if check_password(str(pin or barcode), hashed):
            cache.delete(rl_key)
            return cred.role_assignment.user_id

    _record_failed_attempt(rl_key)
    return None
