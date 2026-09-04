"""
Row-Level-Security helpers for multi-tenant isolation (ADR-0002).

Two enforcement layers:

1. Django ORM guard — :func:`enforce_tenant_scope` and :func:`require_tenant`
   force every queryset to be filtered by ``tenant_id`` at the application
   layer.

2. PostgreSQL policies — :func:`set_tenant_guc` writes the tenant id into a
   session GUC (``app.current_tenant_id`` by default) so RLS policies defined
   in migrations can reference it via ``current_setting()``.
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Optional

from django.conf import settings
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest

logger = logging.getLogger("cybercom.security.rls")


class TenantScopeError(RuntimeError):
    """Raised when a queryset cannot be scoped to a tenant."""


def _tenant_from_request(request: HttpRequest) -> Optional[str]:
    return (
        getattr(request, "tenant_id", None)
        or getattr(getattr(request, "tenant", None), "id", None)
    )


def enforce_tenant_scope(request: HttpRequest, queryset: QuerySet) -> QuerySet:
    """
    Return ``queryset`` filtered by the request's tenant id.

    The tenant id is discovered on ``request.tenant_id`` (populated by
    ``TenantIsolationMiddleware``) or ``request.tenant.id``. If neither is
    present, :class:`TenantScopeError` is raised — callers must not accept
    an unscoped queryset when RLS is expected.
    """
    tenant_id = _tenant_from_request(request)
    if tenant_id is None:
        raise TenantScopeError(
            "enforce_tenant_scope called without request.tenant_id — "
            "TenantIsolationMiddleware must run first."
        )
    return queryset.filter(tenant_id=tenant_id)


def require_tenant(view_or_qs: Any) -> Any:
    """
    Decorator / mixin marker enforcing tenant scoping.

    Usage as a view decorator::

        @require_tenant
        def my_view(request, ...):
            ...

    The wrapped view raises :class:`TenantScopeError` if the request has no
    tenant id.
    """

    if callable(view_or_qs):

        @functools.wraps(view_or_qs)
        def _wrapper(request: HttpRequest, *args: Any, **kwargs: Any):
            if _tenant_from_request(request) is None:
                raise TenantScopeError(
                    f"{view_or_qs.__name__} requires a tenant-scoped request."
                )
            return view_or_qs(request, *args, **kwargs)

        return _wrapper

    raise TypeError(
        "require_tenant must decorate a view callable; got %r" % type(view_or_qs)
    )


def set_tenant_scope(connection, tenant_id: str) -> None:
    """
    Bind the tenant id onto a specific DB connection via ``SET LOCAL``.

    Convenience wrapper for callers that already hold a cursor / connection
    (transaction hooks, background jobs). For request-scoped defaults use
    :func:`set_tenant_guc`.
    """
    guc = getattr(settings, "TENANT_GUC_SETTING", "app.current_tenant_id")
    with connection.cursor() as cursor:
        cursor.execute(f"SET LOCAL {guc} = %s", [str(tenant_id)])


def set_tenant_guc(tenant_id: str, *, local: bool = True) -> None:
    """
    Set the PostgreSQL session variable read by RLS policies.

    Uses ``set_config(name, value, is_local)`` — unlike ``SET``, the setting
    name can be a bind parameter, and it works from the DB-API cursor. With
    ``local=True`` the change is scoped to the current transaction (safe under
    connection pooling but lost in Django's autocommit mode); ``local=False``
    holds it for the connection until reset — what request/job scoping needs.

    No-op on non-PostgreSQL backends (SQLite tests have no GUC / RLS).
    """
    if connection.vendor != "postgresql":
        return
    guc = getattr(settings, "TENANT_GUC_SETTING", "app.current_tenant_id")
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, %s, %s)", [guc, str(tenant_id), local])


def clear_tenant_guc(*, local: bool = True) -> None:
    """Reset the tenant GUC — call after a request / background job finishes."""
    if connection.vendor != "postgresql":
        return
    guc = getattr(settings, "TENANT_GUC_SETTING", "app.current_tenant_id")
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, %s, %s)", [guc, "", local])


def set_session_replication_role(role: str = "replica") -> None:
    """
    Toggle ``session_replication_role`` — used to bypass triggers / RLS during
    controlled data-migration windows. Requires superuser privileges.

    Valid roles: ``origin`` (default), ``replica`` (bypass RLS + triggers),
    ``local``.
    """
    if role not in ("origin", "replica", "local"):
        raise ValueError(f"invalid session_replication_role: {role!r}")
    with connection.cursor() as cursor:
        cursor.execute("SET session_replication_role = %s", [role])
    logger.warning("session_replication_role set to %s — RLS bypassed", role)


def tenant_context(tenant_id: str) -> "_TenantContext":
    """
    Context manager equivalent to :func:`set_tenant_guc` + :func:`clear_tenant_guc`.

    Usage::

        with tenant_context(tenant.id):
            do_background_work()
    """
    return _TenantContext(tenant_id)


class _TenantContext:
    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id

    def __enter__(self) -> "_TenantContext":
        set_tenant_guc(self.tenant_id, local=False)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        clear_tenant_guc(local=False)


class TenantRequiredMixin:
    """
    DRF view mixin that enforces the request has a resolved tenant id.

    Refuses the request with HTTP 403 when :class:`TenantIsolationMiddleware`
    did not populate ``request.tenant_id``. Use on any view that reads or
    writes tenant-scoped data.
    """

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any):  # noqa: D401
        from django.http import JsonResponse

        if _tenant_from_request(request) is None:
            logger.warning(
                "tenant_required.missing",
                extra={"path": request.path},
            )
            return JsonResponse(
                {"error": "tenant_required"}, status=403
            )
        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]


def enforce_on_manager(queryset_getter: Callable[[Any], QuerySet]) -> Callable:
    """
    Decorator for custom manager methods that must be tenant-scoped.

    The wrapped method receives ``request`` as its second positional argument
    (after ``self``) and returns a scoped queryset.
    """

    @functools.wraps(queryset_getter)
    def _wrapper(self: Any, request: HttpRequest, *args: Any, **kwargs: Any) -> QuerySet:
        qs = queryset_getter(self, request, *args, **kwargs)
        return enforce_tenant_scope(request, qs)

    return _wrapper
