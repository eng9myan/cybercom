"""
Default tenant scoping for DRF views.

Two pieces, both deny-by-default so a new view is scoped without anyone
remembering to scope it:

``TenantScopeFilterBackend``
    A DEFAULT_FILTER_BACKENDS entry. Every queryset whose model carries a
    ``tenant_id`` column is narrowed to the caller's tenant. DRF runs
    ``filter_queryset`` for list views *and* inside ``get_object()``, so
    retrieve / update / destroy and any action that calls ``get_object()``
    are covered too.

``TenantObjectGuardMiddleware``
    A ``process_view`` hook for detail routes (``.../<pk>/...``). Many custom
    actions take ``pk`` and hand it straight to a service that does
    ``Model.objects.get(id=pk)`` — they never touch ``get_object()``, so no
    filter backend can see them. The guard resolves the routed viewset's model
    *before* the view runs and answers 404 when the row exists but belongs to
    another tenant, whatever the action body does afterwards.

Shared reference data
    Catalog rows (editions, feature flags, deployment profiles …) are seeded
    once under ``PLATFORM_TENANT_ID`` and read by every tenant. A view opts in
    with ``shared_tenant_ids = (PLATFORM_TENANT_ID,)``: those rows become
    *readable* by all tenants, but unsafe methods still only reach the caller's
    own rows, so a tenant can never edit the shared catalog.

Rows shared with a second tenant
    A view whose rows are deliberately visible to another tenant too (a
    consent granted to a provider, an order routed to a fulfilling pharmacy)
    lists the extra columns in ``tenant_scope_fields``, e.g.
    ``("tenant_id", "granted_to_tenant_id")``. A row matches when ANY of them
    holds the caller's tenant.

Opt-outs
    ``tenant_scope_exempt = True`` on a view skips both pieces. Reserved for
    views that are deliberately cross-tenant and gate access some other way
    (public token-gated endpoints, platform-admin-only consoles).

Platform admins with no tenant selected (``request.tenant_id is None``) see
every tenant — that is the cross-tenant admin console the tenant middleware
already allows. A platform admin who *does* send a tenant is confined to it.
"""
from __future__ import annotations

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import SAFE_METHODS

from platform.api.permissions import _roles

PLATFORM_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def is_tenant_model(model) -> bool:
    if model is None:
        return False
    try:
        field = model._meta.get_field("tenant_id")
    except FieldDoesNotExist:
        return False
    return field.concrete


def is_platform_admin(request) -> bool:
    return "platform_admin" in _roles(request)


def visible_tenant_ids(request, view, method: str) -> list[str] | None:
    """Tenant ids the caller may touch with ``method``; None = no tenant set."""
    tenant_id = getattr(request, "tenant_id", None)
    if not tenant_id:
        return None
    ids = [str(tenant_id)]
    if method in SAFE_METHODS:
        ids.extend(str(t) for t in getattr(view, "shared_tenant_ids", ()) or ())
    return ids


def tenant_q(view, ids: list[str]) -> Q:
    """Rows owned by (or explicitly shared with) one of ``ids``."""
    fields = getattr(view, "tenant_scope_fields", None) or ("tenant_id",)
    q = Q(tenant_id__in=ids)
    for field in fields:
        if field != "tenant_id":
            # shared_tenant_ids only ever apply to the owner column
            q |= Q(**{f"{field}__in": ids[:1]})
    return q


class TenantScopeFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if getattr(view, "tenant_scope_exempt", False):
            return queryset
        if not is_tenant_model(queryset.model):
            return queryset
        ids = visible_tenant_ids(request, view, request.method)
        if ids is None:
            return queryset if is_platform_admin(request) else queryset.none()
        return queryset.filter(tenant_q(view, ids))


class TenantObjectGuardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        cls = getattr(view_func, "cls", None)
        if cls is None or getattr(cls, "tenant_scope_exempt", False):
            return None
        model = getattr(getattr(cls, "queryset", None), "model", None)
        if not is_tenant_model(model):
            return None
        lookup_field = getattr(cls, "lookup_field", "pk")
        url_kwarg = getattr(cls, "lookup_url_kwarg", None) or lookup_field
        if url_kwarg not in view_kwargs:
            return None
        ids = visible_tenant_ids(request, cls, request.method)
        if ids is None:
            # No tenant selected: a platform admin (cross-tenant by design) or
            # an anonymous caller whom the view's permissions will turn away.
            return None
        rows = model._base_manager.filter(**{lookup_field: view_kwargs[url_kwarg]})
        try:
            if not rows.exists() or rows.filter(tenant_q(cls, ids)).exists():
                return None
        except (ValueError, ValidationError):
            return None  # malformed id — let the view produce its own 404/400
        return JsonResponse({"detail": "Not found."}, status=404)
