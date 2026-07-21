from django.db import connection
from django.http import JsonResponse


class TenantIsolationMiddleware:
    """
    Decodes the X-Tenant-ID header injected by Kong API Gateway.
    Sets the postgres session setting `app.current_tenant_id` dynamically.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = request.headers.get("X-Tenant-ID", None)

        # Allow open paths to bypass tenant validation
        if request.path in [
            "/health",
            "/health/liveness",
            "/health/readiness",
            "/api/v1/identity/healthz/",
            "/api/v1/identity/metrics",
            "/api/v1/identity/token/validate/",
        ]:
            return self.get_response(request)

        # Allow public website marketing APIs to bypass tenant validation
        if request.path.startswith("/api/v1/public/"):
            request.tenant_id = None
            return self.get_response(request)

        # Django admin/static/media aren't tenant-scoped by this middleware
        if request.path.startswith("/admin") or request.path.startswith("/static/") or request.path.startswith("/media/"):
            request.tenant_id = None
            return self.get_response(request)

        # CyID (PersonIdentity) is deliberately cross-tenant — a person
        # isn't scoped to any single tenant, that's the whole point of
        # enroll/link-tenant. Same bypass rationale as platform_admin below.
        if request.path.startswith("/api/v1/identity/persons/") and (
            request.path.endswith("/enroll/") or request.path.endswith("/link-tenant/")
        ):
            request.tenant_id = None
            return self.get_response(request)

        # Fallback to check token session payload if header is missing
        if not tenant_id and hasattr(request, "user_session"):
            tenant_id = request.user_session.get("tenant_id")

        if not tenant_id:
            # Platform admins operate cross-tenant by design (e.g. listing
            # every tenant/subscription for the admin panel) — they have no
            # single tenant_id to supply. Previously there was no bypass at
            # all here, so even IsPlatformAdmin-gated cross-tenant endpoints
            # were unreachable with a real token. Skip RLS scoping for them;
            # the DRF permission classes (IsPlatformAdmin/ReadOnlyOrPlatformAdmin)
            # already gate which endpoints a platform_admin may call.
            roles = set(getattr(request, "user_session", {}).get("roles") or [])
            if "platform_admin" in roles:
                request.tenant_id = None
                return self.get_response(request)
            return JsonResponse({"detail": "X-Tenant-ID header or claim is missing."}, status=400)

        # Set thread-safe setting inside PostgreSQL connection pool
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_tenant_id = %s;", [tenant_id])

        request.tenant_id = tenant_id
        return self.get_response(request)
