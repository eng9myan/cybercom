"""
`@tenant_task` — a Celery task that carries a tenant.

Async tasks run in a worker with no request, so the ambient tenant context
(`platform.common.tenant_context`) that `TenantScopedMixin.save()` and the RLS
GUC rely on is empty. `@tenant_task` fixes that: the decorated task takes a
`tenant_id` (first positional arg after `self`, or a `tenant_id=` kwarg) and
runs its body inside `tenant_context(tenant_id)` — and, when
`settings.RLS_ENFORCED`, sets the Postgres session GUC for the task's DB work.

    from platform.common.celery import tenant_task

    @tenant_task(bind=True, max_retries=3)
    def rebuild_report(self, tenant_id, report_id):
        Report.objects.create(name="…")          # tenant_id filled from context

    rebuild_report.delay(tenant_id=str(tid), report_id=str(rid))

`tenant_id` stays in the task's own signature — the decorator only *reads* it to
establish context, it does not consume it. For an existing task that already
loads a tenant-scoped row, `with tenant_context(obj.tenant_id): ...` around the
writes is the lighter retrofit.

If the task is dispatched with an `actor_id=` kwarg the decorator pops it (the
task never sees it) and sets the ambient actor context, so `BaseModel.save()`
fills `created_by` / `updated_by` for a task acting on a user's behalf. Omit it
for a system task — a null actor is the correct "system" marker.
"""
from __future__ import annotations

import contextlib
import functools

from celery import shared_task
from django.conf import settings

from platform.common.actor_context import actor_context
from platform.common.tenant_context import TenantContextMissing, tenant_context


def _peek_tenant_id(args, kwargs, *, bound):
    if "tenant_id" in kwargs:
        return kwargs["tenant_id"]
    # positional: (self, tenant_id, ...) when bound, else (tenant_id, ...)
    idx = 1 if bound else 0
    if len(args) > idx:
        return args[idx]
    raise TenantContextMissing(
        "tenant_task requires a tenant_id — pass it first positionally "
        "(after self, if bind=True) or as tenant_id=."
    )


def tenant_task(*task_args, **task_kwargs):
    """Decorator factory: like `@shared_task(...)` but tenant-aware."""
    bound = bool(task_kwargs.get("bind", False))

    def decorate(func):
        @functools.wraps(func)
        def _run(*args, **kwargs):
            tenant_id = _peek_tenant_id(args, kwargs, bound=bound)
            actor_id = kwargs.pop("actor_id", None)  # decorator-only, hidden from the task
            actor_cm = actor_context(actor_id) if actor_id else contextlib.nullcontext()
            with tenant_context(tenant_id), actor_cm:
                if getattr(settings, "RLS_ENFORCED", False):
                    from platform.security.rls import clear_tenant_guc, set_tenant_guc

                    set_tenant_guc(str(tenant_id), local=False)
                    try:
                        return func(*args, **kwargs)
                    finally:
                        clear_tenant_guc(local=False)
                return func(*args, **kwargs)

        return shared_task(*task_args, **task_kwargs)(_run)

    return decorate
