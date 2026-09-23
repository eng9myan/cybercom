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

        # Public self-serve signup + payment callbacks have no tenant yet —
        # register CREATES the tenant, and gateway webhooks carry no tenant
        # header. Scope them tenant-less (they are AllowAny + throttled).
        if request.path in (
            "/api/v1/tenants/register/", "/api/v1/tenants/demo/",
            "/api/v1/tenants/pricing/", "/api/v1/tenants/healthz/",
            "/api/v1/tenants/metrics",
        ) or request.path.startswith("/api/v1/tenants/payments/"):
            request.tenant_id = None
            return self.get_response(request)

        # Public e-signature portal — a signer has no login, only the
        # unguessable token in the link, and the view resolves the request
        # (and its tenant) cross-tenant by that token, not by header/claim.
        if request.path.startswith("/api/sign/requests/public/"):
            request.tenant_id = None
            return self.get_response(request)

        # Public storefront — an anonymous shopper has no login and no
        # tenant header; the view resolves the tenant itself from the
        # slug in the URL.
        if request.path.startswith("/api/store/"):
            request.tenant_id = None
            return self.get_response(request)

        # Public blog reader — same posture: no login, tenant resolved
        # from the slug in the URL. (/api/v1/blog/ — the authenticated
        # staff CRUD — is a different prefix and stays gated normally.)
        if request.path.startswith("/api/blog/"):
            request.tenant_id = None
            return self.get_response(request)

        # Public forum — guests both read and post with no login (a real
        # Q&A board, unlike blog's read-only public side); tenant resolved
        # from the slug in the URL same as the others. (/api/v1/forum/ —
        # staff moderation — is a different prefix and stays gated.)
        if request.path.startswith("/api/forum/"):
            request.tenant_id = None
            return self.get_response(request)

        # Public live chat widget — polling, no login; tenant resolved from
        # the slug in the URL same as the others. (/api/v1/livechat/ —
        # staff moderation — is a different prefix and stays gated.)
        if request.path.startswith("/api/chat/"):
            request.tenant_id = None
            return self.get_response(request)

        # Public course catalog (eLearning) — same posture: no login,
        # tenant resolved from the slug in the URL. (/api/v1/elearning/ —
        # staff CRUD — is a different prefix and stays gated normally.)
        if request.path.startswith("/api/learn/"):
            request.tenant_id = None
            return self.get_response(request)

        if not tenant_id and hasattr(request, "user_session"):
            tenant_id = request.user_session.get("tenant_id")

        if not tenant_id:
            # Platform admins operate cross-tenant by design. DRF permission
            # classes (IsPlatformAdmin etc.) already gate which endpoints a
            # platform_admin may call — this only skips RLS scoping for them.
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
