"""Value-based approval enforcement (audit HR-4).

Provisioning generates a per-tenant `ApprovalPolicy` per document type with
amount-banded `ApprovalTier` rows (0–500 → Department Manager, 500–5000 →
Procurement Manager, 5000+ → General Manager, …). Nothing consumed them: PO
and payment `approve` actions only checked `IsPlatformAdmin`.

`require_approval_authority()` closes that gap. Given a document type and its
amount it finds the tier band the amount falls in and demands the caller hold
that tier's `approver_role` — as a provisioned `access.Role` assignment or as
a role claim in the token. Platform/tenant admins keep a break-glass bypass.
When a tenant has no policy for the document type, behaviour is unchanged from
before this fix: an admin role is required.
"""

import re
from decimal import Decimal

from rest_framework.exceptions import PermissionDenied

from products.cycom.access.models import RoleAssignment

ADMIN_ROLES = {"platform_admin", "cyidentity_admin", "tenant_admin"}

# A PO / vendor bill has no dedicated policy in the seed matrices — it inherits
# the chain of the request/payment it derives from.
DOC_TYPE_FALLBACKS = {
    "purchase_order": ["purchase_order", "purchase_request"],
    "vendor_bill": ["vendor_bill", "payment"],
    "payment": ["payment"],
    "purchase_request": ["purchase_request"],
}


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _claim_roles(request):
    claims = getattr(request, "auth_claims", {}) or {}
    roles = set(claims.get("realm_access", {}).get("roles", []))
    roles |= set(claims.get("roles", []) or [])
    session = getattr(request, "user_session", None) or {}
    roles |= set(session.get("roles", []) or [])
    return roles


def is_admin(request):
    return bool({_slug(r) for r in _claim_roles(request)} & ADMIN_ROLES)


def _user_id(request):
    claims = getattr(request, "auth_claims", {}) or {}
    session = getattr(request, "user_session", None) or {}
    return claims.get("sub") or session.get("user_id")


def user_holds_role(request, tenant_id, role_name):
    """True if the caller holds `role_name` — matched case/format-insensitively
    against their token role claims or their provisioned Role assignments."""
    target = _slug(role_name)
    if target in {_slug(r) for r in _claim_roles(request)}:
        return True
    user_id = _user_id(request)
    if not user_id or tenant_id is None:
        return False
    held = RoleAssignment.objects.filter(
        tenant_id=tenant_id, user_id=str(user_id)
    ).values_list("role__name", flat=True)
    return any(_slug(name) == target for name in held)


def _resolve_policy(tenant_id, document_type):
    # Imported here so `products.cycom.access` doesn't hard-depend on the
    # provisioning app at import time (keeps app-loading order flexible).
    from platform.provisioning.models import ApprovalPolicy

    for dt in DOC_TYPE_FALLBACKS.get(document_type, [document_type]):
        policy = (
            ApprovalPolicy.objects.filter(
                tenant_id=tenant_id, document_type=dt, is_active=True
            )
            .prefetch_related("tiers")
            .first()
        )
        if policy:
            return policy
    return None


def required_approver_role(tenant_id, document_type, amount):
    """The `approver_role` for the tier band `amount` falls in, or None when the
    tenant has no active policy for `document_type`."""
    policy = _resolve_policy(tenant_id, document_type)
    if policy is None:
        return None
    amount = Decimal(str(amount or 0))
    tiers = sorted(policy.tiers.all(), key=lambda t: (t.sequence, t.threshold_min))
    for tier in tiers:
        low = tier.threshold_min or Decimal("0")
        high = tier.threshold_max
        if amount >= low and (high is None or amount < high):
            return tier.approver_role
    # Amount above every band's ceiling → the last (highest) tier governs.
    return tiers[-1].approver_role if tiers else None


def require_approval_authority(request, tenant_id, document_type, amount):
    """Raise PermissionDenied unless the caller may approve a `document_type`
    document of this `amount`. Admins always pass."""
    if is_admin(request):
        return

    role_name = required_approver_role(tenant_id, document_type, amount)
    if role_name is None:
        raise PermissionDenied(
            "Approving this document requires an administrator role "
            "(no approval policy is configured for this document type)."
        )
    if not user_holds_role(request, tenant_id, role_name):
        raise PermissionDenied(
            f"Amount {amount} requires approval by role '{role_name}'."
        )
