"""
Ambient tenant context — the source of truth for `tenant_id` on writes.

Set once per request (by TenantIsolationMiddleware) and per Celery task, read
by `TenantScopedManager.create()` so a service that forgets to pass `tenant_id`
gets it from context instead of failing with a bare `IntegrityError` — or, if
there is genuinely no context, fails loudly with `TenantContextMissing`.

See docs/blueprint/specs/canonical-data-model-v1.md §2.2.
"""
from __future__ import annotations

import contextlib
from contextvars import ContextVar

_current_tenant: ContextVar[object | None] = ContextVar("cybercom_current_tenant", default=None)


class TenantContextMissing(RuntimeError):
    """Raised when a tenant-scoped write has neither an explicit tenant_id nor
    an ambient tenant context."""


def set_current_tenant(tenant_id) -> None:
    _current_tenant.set(tenant_id)


def get_current_tenant():
    return _current_tenant.get()


def clear_current_tenant() -> None:
    _current_tenant.set(None)


@contextlib.contextmanager
def tenant_context(tenant_id):
    """`with tenant_context(tid): ...` — for management commands, tests, jobs."""
    token = _current_tenant.set(tenant_id)
    try:
        yield
    finally:
        _current_tenant.reset(token)
