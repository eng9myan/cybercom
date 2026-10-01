"""
DevAuthMiddleware — a no-Keycloak stand-in for CyIdentityAuthMiddleware,
used ONLY by core.settings_dev. Mirrors cycom/core/dev_auth.py and
CyEd/core/settings_dev.py's precedent for this project family.

It performs NO signature verification. It reads claims from a Bearer
token if one is present (so the frontend's own unsigned dev JWT — minted
in cymart-web's /api/dev-login route, same shape as cycom's
lib/cycomServer.ts — flows through), otherwise it injects a default dev
identity. Either way it populates request.user_session exactly like the
real middleware, so downstream services behave identically.

Hard safety gate: refuses to activate unless DEBUG and CYMART_DEV_AUTH=1.
"""

import base64
import json
import os

from django.conf import settings
from rest_framework.authentication import BaseAuthentication

_PUBLIC_PREFIXES = ("/api/v1/public/", "/admin", "/static/", "/media/")
_PUBLIC_EXACT = {
    "/health", "/health/liveness", "/health/readiness",
    "/api/v1/identity/healthz/", "/api/v1/identity/metrics",
    "/api/v1/identity/token/validate/",
}


def _decode_unverified(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)  # pad base64url
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return {}


class DevAuthMiddleware:
    def __init__(self, get_response):
        if not (settings.DEBUG and os.environ.get("CYMART_DEV_AUTH") == "1"):
            raise RuntimeError(
                "DevAuthMiddleware refuses to load without DEBUG=True and "
                "CYMART_DEV_AUTH=1. Never reference this from production settings."
            )
        self.get_response = get_response

    def __call__(self, request):
        if request.path in _PUBLIC_EXACT or request.path.startswith(_PUBLIC_PREFIXES):
            return self.get_response(request)

        auth_header = request.headers.get("Authorization", "")
        claims = {}
        if auth_header.startswith("Bearer "):
            claims = _decode_unverified(auth_header.split(" ", 1)[1])

        request.auth_claims = claims
        request.user_session = {
            "user_id": claims.get("sub", "dev-user"),
            "email": claims.get("email", "dev@cymart.dev"),
            "tenant_id": claims.get("tenant_id"),
            "roles": claims.get("roles")
            or claims.get("realm_access", {}).get("roles", ["customer"]),
            "permissions": claims.get("permissions", []),
        }
        return self.get_response(request)


class DevSessionAuthentication(BaseAuthentication):
    """DRF's own auth layer is separate from the middleware above — the
    middleware sets request.user_session, but IsAuthenticated checks
    request.user.is_authenticated, which stays False (AnonymousUser)
    unless something in DEFAULT_AUTHENTICATION_CLASSES turns
    user_session into a user. Same role core.settings_test.
    TestJWTAuthentication plays for pytest; this is that class's
    dev-server counterpart. Wired in via settings_dev.py only."""

    def authenticate(self, request):
        user_session = getattr(request._request, "user_session", None)
        if not user_session:
            return None

        class DevUser:
            is_authenticated = True
            id = user_session.get("user_id", "dev-user")

            def __str__(self):
                return str(self.id)

        return (DevUser(), None)
