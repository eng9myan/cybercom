"""
Website Public API — Permissions.
All public endpoints use AllowAny. Optional JWT enrichment for analytics.
"""

from rest_framework.permissions import AllowAny, BasePermission


class IsPublicEndpoint(AllowAny):
    """
    Explicitly marks an endpoint as intentionally public.
    No authentication required; used for marketing content APIs.
    """

    message = "This endpoint is publicly accessible."


class IsAdminOrReadOnly(BasePermission):
    """
    Admin users can write; all others can only read.
    Used for the API health/status endpoint.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(request.user and request.user.is_staff)
