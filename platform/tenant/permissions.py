"""
CyberCom Multi-Tenant Framework — DRF Permission Classes.
ADR-0002: cross-tenant isolation enforcement at API layer.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPlatformAdmin(BasePermission):
    """Requires platform_admin or tenant_admin role in JWT realm_access claims."""

    ADMIN_ROLES = {"platform_admin", "cyidentity_admin", "tenant_admin"}

    def has_permission(self, request, view) -> bool:
        claims = getattr(request, "auth_claims", {})
        realm_roles = set(claims.get("realm_access", {}).get("roles", []))
        return bool(realm_roles & self.ADMIN_ROLES)


class ReadOnlyOrPlatformAdmin(BasePermission):
    """Safe methods always pass; mutations require admin role."""

    ADMIN_ROLES = {"platform_admin", "tenant_admin"}

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        claims = getattr(request, "auth_claims", {})
        realm_roles = set(claims.get("realm_access", {}).get("roles", []))
        return bool(realm_roles & self.ADMIN_ROLES)


class IsTenantOwner(BasePermission):
    """
    Object-level: request tenant_id claim must match the object's tenant.
    Allows platform admins to bypass.
    """

    BYPASS_ROLES = {"platform_admin"}

    def has_object_permission(self, request, view, obj) -> bool:
        claims = getattr(request, "auth_claims", {})
        realm_roles = set(claims.get("realm_access", {}).get("roles", []))
        if realm_roles & self.BYPASS_ROLES:
            return True
        claim_tenant_id = str(claims.get("tenant_id", ""))
        obj_tenant_id = str(getattr(obj, "tenant_id", getattr(obj, "id", "")))
        return claim_tenant_id == obj_tenant_id


class NoCrossTenantAccess(BasePermission):
    """
    Prevents a tenant from accessing another tenant's data.
    Enforced at the viewset queryset level; this provides an extra API-layer guard.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        claims = getattr(request, "auth_claims", {})
        claim_tenant_id = str(claims.get("tenant_id", ""))
        if not claim_tenant_id:
            return True  # let other permission classes handle unauthenticated
        tenant = getattr(obj, "tenant", obj)
        return str(tenant.id) == claim_tenant_id


class CanProvisionTenant(BasePermission):
    """Only platform admins may provision new tenants."""

    def has_permission(self, request, view) -> bool:
        claims = getattr(request, "auth_claims", {})
        realm_roles = set(claims.get("realm_access", {}).get("roles", []))
        return "platform_admin" in realm_roles


class CanTerminateTenant(BasePermission):
    """Only platform admins may terminate or decommission tenants."""

    def has_permission(self, request, view) -> bool:
        claims = getattr(request, "auth_claims", {})
        realm_roles = set(claims.get("realm_access", {}).get("roles", []))
        return "platform_admin" in realm_roles
