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
        tenant_id = request.headers.get('X-Tenant-ID', None)
        
        # Allow open paths to bypass tenant validation
        if request.path in ['/health', '/health/liveness', '/health/readiness']:
            return self.get_response(request)

        # Fallback to check token session payload if header is missing
        if not tenant_id and hasattr(request, 'user_session'):
            tenant_id = request.user_session.get('tenant_id')

        if not tenant_id:
            return JsonResponse({"detail": "X-Tenant-ID header or claim is missing."}, status=400)

        # Set thread-safe setting inside PostgreSQL connection pool
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.current_tenant_id = %s;", [tenant_id])

        request.tenant_id = tenant_id
        return self.get_response(request)
