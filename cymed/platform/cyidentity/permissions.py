"""
CyIdentity permissions.

Two layers:
  - RealmPermission / RolePermission / BreakGlassPermission:
    object-level permission checks on CyIdentity models.
  - TokenHasRealmRole / TokenHasScope:
    JWT-claim-based checks that work with the validated bearer token.
"""

from __future__ import annotations

from rest_framework import permissions

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class IsPlatformAdmin(permissions.BasePermission):
    """Allows access only to callers carrying the `platform_admin` role claim."""

    message = "Platform admin role required."

    def has_permission(self, request, view) -> bool:
        token = getattr(request, "auth_claims", None) or {}
        roles = set(token.get("realm_access", {}).get("roles", []) or [])
        return "platform_admin" in roles or "cyidentity_admin" in roles


class ReadOnlyOrPlatformAdmin(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        token = getattr(request, "auth_claims", None) or {}
        roles = set(token.get("realm_access", {}).get("roles", []) or [])
        return "platform_admin" in roles or "cyidentity_admin" in roles


class IsTenantScoped(permissions.BasePermission):
    """Object-level: caller must be operating inside the tenant of the object."""

    def has_object_permission(self, request, view, obj) -> bool:
        token = getattr(request, "auth_claims", None) or {}
        claim_tenant = token.get("tenant_id")
        obj_tenant = getattr(obj, "tenant_id", None)
        if claim_tenant is None or obj_tenant is None:
            return False
        return str(claim_tenant).lower() == str(obj_tenant).lower()


class BreakGlassRequiresDualApproval(permissions.BasePermission):
    """Break-glass approve/activate require both approver + second_approver set."""

    def has_permission(self, request, view) -> bool:
        if view.action not in {"approve", "activate"}:
            return True
        body = request.data if isinstance(request.data, dict) else {}
        if view.action == "approve":
            return bool(body.get("approver")) and bool(body.get("second_approver"))
        return True


class TokenHasRealmRole(permissions.BasePermission):
    required_role: str = ""

    def has_permission(self, request, view) -> bool:
        token = getattr(request, "auth_claims", None) or {}
        roles = set(token.get("realm_access", {}).get("roles", []) or [])
        return self.required_role in roles


class TokenHasScope(permissions.BasePermission):
    required_scope: str = ""

    def has_permission(self, request, view) -> bool:
        token = getattr(request, "auth_claims", None) or {}
        scope = token.get("scope") or ""
        scopes = set(scope.split()) if isinstance(scope, str) else set(token.get("scp", []) or [])
        return self.required_scope in scopes
