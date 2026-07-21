from rest_framework.permissions import BasePermission


class IsAuthenticatedViaClaims(BasePermission):
    """
    DEFAULT_AUTHENTICATION_CLASSES is [] repo-wide, so DRF's IsAuthenticated
    (which reads request.user) never passes. CyIdentityAuthMiddleware sets
    request.auth_claims instead — check that.
    """

    def has_permission(self, request, view) -> bool:
        return getattr(request, "auth_claims", None) is not None
