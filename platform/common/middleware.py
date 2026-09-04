"""
TenantContextMiddleware — the single place that binds the request's tenant to
both isolation layers for the duration of the request, and unbinds them after:

  1. the ambient tenant context (`platform.common.tenant_context`), read by
     `TenantScopedMixin.save()` to fill `tenant_id` when a caller forgets it;
  2. the PostgreSQL session GUC (`app.current_tenant_id`), read by the RLS
     policies (`platform.security.rls_ddl`) — only touched when RLS is enforced
     and the backend is PostgreSQL;
  3. the ambient actor context (`platform.common.actor_context`), read by
     `BaseModel.save()` to fill `created_by` / `updated_by` — from the JWT
     `user_session["user_id"]` (the `sub` claim).

Must run AFTER whatever sets `request.tenant_id` and `request.user_session`
(CyIdentityAuthMiddleware + the product's TenantIsolationMiddleware). The reset
in `finally` matters: WSGI reuses worker threads and pooled DB connections, so a
value left set would leak to the next request on the same thread/connection.
"""
from __future__ import annotations

import logging

from django.conf import settings

from platform.common.actor_context import _current_actor, _coerce
from platform.common.tenant_context import _current_tenant

logger = logging.getLogger("platform.common.tenant_ctx")


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._rls = bool(getattr(settings, "RLS_ENFORCED", False))

    def __call__(self, request):
        tid = getattr(request, "tenant_id", None)
        actor = _coerce(getattr(request, "user_session", {}).get("user_id"))
        tenant_token = _current_tenant.set(tid)
        actor_token = _current_actor.set(actor)
        if self._rls and tid:
            self._set_guc(str(tid))
        try:
            return self.get_response(request)
        finally:
            _current_tenant.reset(tenant_token)
            _current_actor.reset(actor_token)
            if self._rls and tid:
                self._set_guc("")

    @staticmethod
    def _set_guc(value: str) -> None:
        # session-scoped (is_local=False): survives Django's autocommit mode,
        # where a SET LOCAL would be discarded before the view's queries run.
        from platform.security.rls import clear_tenant_guc, set_tenant_guc

        try:
            if value:
                set_tenant_guc(value, local=False)
            else:
                clear_tenant_guc(local=False)
        except Exception:  # pragma: no cover - never fail a request on GUC housekeeping
            logger.exception("tenant GUC update failed")
