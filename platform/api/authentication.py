"""
M-7 — production DRF authentication.

`shared.auth.auth_middleware.CyIdentityAuthMiddleware` validates the RS256
bearer token and populates `request.user_session` / `request.auth_claims`,
but nothing bridged that to `request.user`, so stock `IsAuthenticated`
(which reads `request.user.is_authenticated`) denied every gated endpoint in
production — the API only worked under the test settings' `TestJWTAuthentication`.

`ClaimsAuthentication` closes that gap: it turns a validated `user_session`
into an authenticated principal carrying the caller's id, roles and tenant,
so permission classes have a real actor to reason about.
"""
from __future__ import annotations

from rest_framework.authentication import BaseAuthentication


class ClaimsPrincipal:
    """A lightweight authenticated user backed by the CyIdentity token claims.

    Not a Django ORM user — CyberCom identities live in Keycloak / CyIdentity,
    not `auth_user`. Exposes just what DRF and the permission layer need.
    """

    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, session: dict, claims: dict):
        self._session = session or {}
        self._claims = claims or {}
        self.id = self._session.get("user_id") or self._claims.get("sub") or ""
        self.pk = self.id
        self.username = self._session.get("email") or self._claims.get("email") or self.id
        self.email = self._session.get("email") or self._claims.get("email") or ""
        self.tenant_id = self._session.get("tenant_id") or self._claims.get("tenant_id")
        self.roles = set(
            self._session.get("roles")
            or self._claims.get("realm_access", {}).get("roles", [])
            or []
        )
        self.permissions = set(self._session.get("permissions") or [])
        self.campus_ids = list(self._session.get("campus_ids") or [])

    def __str__(self) -> str:
        return self.username or "claims-principal"

    def has_role(self, *names) -> bool:
        return bool(self.roles.intersection(names))


class ClaimsAuthentication(BaseAuthentication):
    """Bridge `request.user_session` (set by CyIdentityAuthMiddleware) → DRF.

    Returns None when there is no session so DRF falls through to the next
    auth class / treats the request as anonymous (the permission layer then
    decides). Never raises — the middleware already rejected bad tokens with
    a 401 before the view is reached.
    """

    def authenticate(self, request):
        session = getattr(request, "user_session", None) or getattr(
            request._request, "user_session", None
        )
        if not session:
            return None
        claims = getattr(request, "auth_claims", None) or getattr(
            request._request, "auth_claims", None
        ) or {}
        return (ClaimsPrincipal(session, claims), None)
