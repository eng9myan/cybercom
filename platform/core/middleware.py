"""
Tenant resolution for the standalone platform project — a pared-down copy of
the product projects' `core.middleware.tenant.TenantIsolationMiddleware`.

Resolves `request.tenant_id` from the `X-Tenant-ID` header or the JWT
`tenant_id` claim (set on `request.user_session` by
`shared.auth.auth_middleware.CyIdentityAuthMiddleware`). Platform admins and
the deliberately cross-tenant surfaces (public signup, CyID persons/wallet)
run with `tenant_id = None`.

Must sit AFTER CyIdentityAuthMiddleware and BEFORE
`platform.common.middleware.TenantContextMiddleware`.
"""
from django.http import JsonResponse

_OPEN_PATHS = {
    "/health",
    "/health/liveness",
    "/health/readiness",
    "/metrics",
    "/api/v1/identity/healthz/",
    "/api/v1/identity/metrics",
    "/api/v1/identity/token/validate/",
}

_CROSS_TENANT_PREFIXES = (
    "/admin",
    "/static/",
    "/media/",
    "/api/v1/public/",
    "/api/v1/wallet/",
    "/api/v1/commerce/checkout/",
)


class TenantIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path in _OPEN_PATHS:
            return self.get_response(request)

        if path.startswith(_CROSS_TENANT_PREFIXES):
            request.tenant_id = None
            return self.get_response(request)

        if path.startswith("/api/v1/identity/persons/") and (
            path.endswith("/enroll/") or path.endswith("/link-tenant/")
        ):
            request.tenant_id = None
            return self.get_response(request)

        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id and hasattr(request, "user_session"):
            tenant_id = request.user_session.get("tenant_id")

        if not tenant_id:
            roles = set(getattr(request, "user_session", {}).get("roles") or [])
            if "platform_admin" in roles:
                request.tenant_id = None
                return self.get_response(request)
            return JsonResponse(
                {"detail": "X-Tenant-ID header or claim is missing."}, status=400
            )

        request.tenant_id = tenant_id
        return self.get_response(request)
