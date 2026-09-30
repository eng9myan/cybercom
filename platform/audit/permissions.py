"""
Audit & Compliance permission classes.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def _roles(request) -> set:
    claims = getattr(request, "auth_claims", {}) or {}
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    session = getattr(request, "user_session", None) or {}
    return set(realm_roles) | set(session.get("roles", []))


def _authenticated(request) -> bool:
    """Either Django session/user auth (cymed/cyed) or claims-based auth
    (cycom's CyIdentity middleware sets request.auth_claims, never
    request.user) -- the old check only knew the former, so every cycom
    caller got 403 on the audit list endpoints."""
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return True
    return bool(getattr(request, "auth_claims", None))


# Roles allowed to *read* audit trails (always within their own tenant --
# see views.TenantScopedAuditMixin). Audit trails record who did what to
# which record (incl. PHI access in cymed), so they are not readable by
# every authenticated user.
AUDIT_READ_ROLES = {"platform_admin", "audit_admin", "cyidentity_admin", "compliance_officer", "tenant_admin"}


def caller_tenant_id(request):
    """The caller's tenant, however the product resolved it; None if unknown."""
    tid = getattr(request, "tenant_id", None)
    if tid:
        return tid
    claims = getattr(request, "auth_claims", None) or {}
    if claims.get("tenant_id"):
        return claims["tenant_id"]
    return getattr(getattr(request, "user", None), "tenant_id", None)


def is_platform_admin(request) -> bool:
    return "platform_admin" in _roles(request)


class IsAuditAdmin(BasePermission):
    """platform_admin or audit_admin role."""

    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "audit_admin", "cyidentity_admin"})


class IsComplianceOfficer(BasePermission):
    """platform_admin, audit_admin, or compliance_officer."""

    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "audit_admin", "compliance_officer"})


class CanReadAudit(BasePermission):
    """Read-only operations that happen to be POSTs (e.g. search)."""

    def has_permission(self, request, view):
        return _authenticated(request) and bool(_roles(request) & AUDIT_READ_ROLES)


class ReadOnlyOrAuditAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return _authenticated(request) and bool(_roles(request) & AUDIT_READ_ROLES)
        return bool(_roles(request) & {"platform_admin", "audit_admin"})


class CanCreateLegalHold(BasePermission):
    """Legal hold creation requires platform_admin or legal_hold_admin."""

    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "legal_hold_admin", "audit_admin"})


class CanReleaseLegalHold(BasePermission):
    """Release requires platform_admin only."""

    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin"})


class CanExportAuditLogs(BasePermission):
    """Export requires audit_admin or compliance_officer."""

    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "audit_admin", "compliance_officer"})
