"""
Audit & Compliance permission classes.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


def _roles(request) -> set:
    claims = getattr(request, "auth_claims", {}) or {}
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    return set(realm_roles)


class IsAuditAdmin(BasePermission):
    """platform_admin or audit_admin role."""
    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "audit_admin", "cyidentity_admin"})


class IsComplianceOfficer(BasePermission):
    """platform_admin, audit_admin, or compliance_officer."""
    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "audit_admin", "compliance_officer"})


class ReadOnlyOrAuditAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
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
