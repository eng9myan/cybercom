"""
TenantContextMiddleware — publishes `request.tenant_id` into the ambient
tenant context (`platform.common.tenant_context`) for the duration of the
request, then resets it.

Must run AFTER whatever middleware sets `request.tenant_id` (the product's
TenantIsolationMiddleware). With it in place, a tenant-scoped model created
anywhere in the request (a service that forgot `tenant_id=`, a signal handler,
a nested call) gets the right tenant automatically via
`TenantScopedMixin.save()`.

The reset in `finally` matters: WSGI reuses worker threads, and a ContextVar
set without reset would leak the previous request's tenant to the next one on
the same thread.
"""
from __future__ import annotations

from platform.common.tenant_context import _current_tenant


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_tenant.set(getattr(request, "tenant_id", None))
        try:
            return self.get_response(request)
        finally:
            _current_tenant.reset(token)
