from django.db import connection
from django.http import JsonResponse


class TenantIsolationMiddleware:
    """
    Decodes the X-Tenant-ID header (injected by the API gateway) or falls back
    to the authenticated session's tenant. Sets the postgres session setting
    `app.current_tenant_id` when on postgres.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = request.headers.get("X-Tenant-ID", None)

        if request.path in [
            "/health",
            "/health/liveness",
            "/health/readiness",
            "/api/v1/identity/healthz/",
            "/api/v1/identity/metrics",
            "/api/v1/identity/token/validate/",
        ]:
            return self.get_response(request)

        if request.path.startswith("/admin") or request.path.startswith("/static/") or request.path.startswith("/media/"):
            request.tenant_id = None
            return self.get_response(request)

        # Public endpoints have no tenant by definition — the caller is an
        # outside system (a payment gateway posting a webhook) with no CyEd
        # account and no way to know what a tenant is. CyIdentityAuthMiddleware
        # already lets this prefix through; without the matching exemption here
        # every such request would 400 on the missing header before reaching a
        # view. Views under this prefix must resolve their own tenant from the
        # record the request refers to, and must authenticate themselves.
        if request.path.startswith("/api/v1/public/"):
            request.tenant_id = None
            return self.get_response(request)

        # The header is only a hint. When the caller presented a verified
        # token, the token's tenant claim is authoritative: a tenant-A token
        # carrying `X-Tenant-ID: <B>` must not be served as tenant B. Without
        # this check the header alone chose the tenant for every queryset AND
        # for the RLS GUC below, so any authenticated user could read another
        # tenant's data by editing one header. Platform admins are the one
        # role that legitimately operates cross-tenant via the header.
        session = getattr(request, "user_session", None) or {}
        token_tenant = session.get("tenant_id")
        if tenant_id and token_tenant and str(tenant_id) != str(token_tenant):
            if "platform_admin" not in set(session.get("roles") or []):
                return JsonResponse(
                    {"detail": "X-Tenant-ID does not match the authenticated tenant."},
                    status=403,
                )
        if not tenant_id and token_tenant:
            tenant_id = token_tenant

        if not tenant_id:
            # Platform admins operate cross-tenant by design; DRF permission
            # classes still gate which endpoints they may call.
            roles = set(getattr(request, "user_session", {}).get("roles") or [])
            if "platform_admin" in roles:
                request.tenant_id = None
                return self.get_response(request)
            return JsonResponse({"detail": "X-Tenant-ID header or claim is missing."}, status=400)

        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_tenant_id = %s;", [tenant_id])

        request.tenant_id = tenant_id
        return self.get_response(request)
