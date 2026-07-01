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
                options={"require": ["exp", "iat", "sub"]},
            )
            request.auth_claims = payload
            request.user_session = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "tenant_id": payload.get("tenant_id"),
                "roles": payload.get("roles") or payload.get("realm_access", {}).get("roles", []),
                "permissions": payload.get("permissions", [])
            }
        except ExpiredSignatureError:
            return JsonResponse({"detail": "Token has expired."}, status=401)
        except InvalidTokenError:
            return JsonResponse({"detail": "Invalid token."}, status=401)

        return self.get_response(request)
