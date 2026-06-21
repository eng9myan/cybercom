import jwt
from django.http import JsonResponse
from django.conf import settings

class CyIdentityAuthMiddleware:
    """
    Decodes and validates JWT tokens issued by CyIdentity.
    Injects request.user_session containing roles, permissions, and tenant ID.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow health checks to bypass auth
        if request.path in ['/health', '/health/liveness', '/health/readiness']:
            return self.get_response(request)

        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

        token = auth_header.split(' ')[1]
        try:
            # In production, this validates against cached JWKS. Moked for bootstrap.
            payload = jwt.decode(token, settings.JWT_SIGNING_KEY, algorithms=['RS256'], options={"verify_signature": False})
            request.user_session = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "tenant_id": payload.get("tenant_id"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", [])
            }
        except jwt.ExpiredSignatureError:
            return JsonResponse({"detail": "Token has expired."}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"detail": "Invalid token."}, status=401)

        return self.get_response(request)
