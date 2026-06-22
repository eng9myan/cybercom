"""
API Framework permission classes. ADR-0003 S8 / ADR-0030 S3.3.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


def _roles(request) -> set:
    claims = getattr(request, "auth_claims", {}) or {}
    return set(claims.get("realm_access", {}).get("roles", []))


class IsApiAdmin(BasePermission):
    """platform_admin or api_admin."""
    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "api_admin"})


class IsApiOwner(BasePermission):
    """api_admin or api_owner."""
    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "api_admin", "api_owner"})


class ReadOnlyOrApiAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(_roles(request) & {"platform_admin", "api_admin"})


class HasApiKeyAuth(BasePermission):
    """Request carries a valid API key in Authorization: Bearer ck_..."""
    def has_permission(self, request, view):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ck_"):
            return True  # Fall through to JWT auth
        raw_key = auth[7:]
        from .services import ApiKeyService
        key = ApiKeyService().verify(raw_key)
        if key:
            request.api_key = key
            return True
        return False


class CanManageWebhooks(BasePermission):
    def has_permission(self, request, view):
        return bool(_roles(request) & {"platform_admin", "api_admin", "api_owner", "developer"})


class CanViewApiCatalog(BasePermission):
    def has_permission(self, request, view):
        return True  # Public catalog is readable
