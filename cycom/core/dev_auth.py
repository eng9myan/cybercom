"""
DevAuthMiddleware — a no-Keycloak stand-in for CyIdentityAuthMiddleware,
used ONLY by core.settings_dev.

It performs NO signature verification. It reads claims from a Bearer token if
one is present (so the frontend's fake dev JWT flows through), otherwise it
injects a default dev identity. Either way it populates request.user_session
exactly like the real middleware, so downstream tenant isolation and viewsets
behave identically.

Hard safety gate: refuses to activate unless DEBUG and CYCOM_DEV_AUTH=1.
"""

import base64
import json
import os

from django.conf import settings
from django.http import JsonResponse

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
        if not (settings.DEBUG and os.environ.get("CYCOM_DEV_AUTH") == "1"):
            raise RuntimeError(
                "DevAuthMiddleware refuses to load without DEBUG=True and CYCOM_DEV_AUTH=1. "
                "Never reference this from production settings."
            )
        self.get_response = get_response
        self.dev_tenant = getattr(settings, "DEV_TENANT_ID", "11111111-1111-1111-1111-111111111111")

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
            "email": claims.get("email", "admin@cycom.dev"),
            "tenant_id": claims.get("tenant_id", self.dev_tenant),
            "roles": claims.get("roles")
            or claims.get("realm_access", {}).get("roles", ["tenant_admin"]),
            "permissions": claims.get("permissions", []),
        }
        return self.get_response(request)
