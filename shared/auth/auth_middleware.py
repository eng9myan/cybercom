import jwt
from jwt import PyJWKClient, ExpiredSignatureError, InvalidTokenError
from django.http import JsonResponse
from django.conf import settings

# JWKS client is module-level so the key set is cached across requests.
_jwks_client: PyJWKClient | None = None

def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.CYIDENTITY_JWKS_URI, cache_keys=True)
    return _jwks_client


class CyIdentityAuthMiddleware:
    """
    Validates RS256 JWT tokens issued by CyIdentity/Keycloak via JWKS.
    Injects request.user_session containing roles, permissions, and tenant ID.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in [
            '/health', '/health/liveness', '/health/readiness',
            '/api/v1/identity/healthz/', '/api/v1/identity/metrics',
            '/api/v1/identity/token/validate/'
        ]:
            return self.get_response(request)

        if request.path.startswith('/api/v1/public/'):
            return self.get_response(request)

        # Public self-serve subscription signup + payment gateway callbacks.
        # AllowAny at the view (throttled): a brand-new customer has no token
        # yet, and a gateway posting a webhook never carries a user token.
        # Without this, the production auth middleware 401s them before the
        # view — the dev-auth shim masked this on the no-Docker path.
        if request.path in (
            '/api/v1/tenants/register/', '/api/v1/tenants/demo/',
            '/api/v1/tenants/pricing/', '/api/v1/tenants/healthz/',
            '/api/v1/tenants/metrics',
        ) or request.path.startswith('/api/v1/tenants/payments/'):
            return self.get_response(request)

        # CyID self-service: a person enrolling has no token yet by
        # definition, and link-tenant proves identity itself via a real
        # password check (CyIDService._verify_home_credential) rather than
        # a bearer token — same AllowAny posture as /api/v1/public/*.
        if request.path.startswith('/api/v1/identity/persons/') and (
            request.path.endswith('/enroll/') or request.path.endswith('/link-tenant/')
        ):
            return self.get_response(request)

        if request.path.startswith('/admin') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

        token = auth_header.split(' ')[1]
        try:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                # PyJWT rejects any token carrying an `aud` claim unless
                # `audience=` is supplied or aud verification is explicitly
                # turned off — every real Keycloak token has `aud`, so this
                # gate rejected 100% of real tokens with InvalidAudienceError
                # until now. This service layer is meant to accept tokens
                # from multiple CyIdentity clients (no single expected
                # audience), so disable aud checking rather than pin one.
                options={"require": ["exp", "iat", "sub"], "verify_aud": False},
            )
            request.auth_claims = payload
            request.user_session = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "tenant_id": payload.get("tenant_id"),
                "roles": payload.get("roles") or payload.get("realm_access", {}).get("roles", []),
                "permissions": payload.get("permissions", []),
                # Campuses this user is bound to, for multi-campus groups where
                # one tenant runs many sites. Dropping this claim silently
                # disabled every campus-scoping check downstream: the scoping
                # helper read a key that was never populated, so it always
                # resolved to "sees everything" and looked correct in review.
                "campus_ids": payload.get("campus_ids") or [],
            }
        except ExpiredSignatureError:
            return JsonResponse({"detail": "Token has expired."}, status=401)
        except InvalidTokenError:
            return JsonResponse({"detail": "Invalid token."}, status=401)

        return self.get_response(request)
