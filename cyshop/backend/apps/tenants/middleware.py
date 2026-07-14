import threading
from django.http import JsonResponse
from .models import Tenant

_thread_locals = threading.local()

def get_current_tenant_id():
    """Helper to retrieve the current thread-local bound tenant ID."""
    return getattr(_thread_locals, 'tenant_id', None)

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = request.headers.get('X-Tenant-ID')
        
        # Fallback to subdomain logic if header is not present
        if not tenant_id:
            host_parts = request.get_host().split('.')
            if len(host_parts) > 2:
                subdomain = host_parts[0]
                try:
                    tenant = Tenant.objects.get(subdomain=subdomain)
                    tenant_id = str(tenant.id)
                except Tenant.DoesNotExist:
                    tenant_id = None

        if tenant_id:
            request.tenant_id = tenant_id
            _thread_locals.tenant_id = tenant_id
        else:
            request.tenant_id = None
            _thread_locals.tenant_id = None

        # Exclude administrative views, login, and registration checks from strict tenant checks
        if not request.tenant_id and not (
            request.path.startswith('/admin/') or 
            request.path.startswith('/api/v1/identity/login/') or
            request.path.startswith('/api/v1/identity/register/') or
            request.path.startswith('/api/v1/tenants/register/')
        ):
            return JsonResponse({"error": "Missing or invalid X-Tenant-ID header context"}, status=400)

        response = self.get_response(request)
        return response
