"""
Generic tenant-scoped ViewSet base, for platform-level apps (shared across
cycom/cymed/...) that need the same tenant isolation cycom's own
`core.viewsets.TenantScopedModelViewSet` provides product-locally.

Ported here because `platform.provisioning.views` imported `core.permissions`/
`core.viewsets` directly -- product-specific module paths that don't exist
when `platform.provisioning` is loaded by the standalone `platform` test
project (vs. a real product's Django project where `core` is that
product's own settings package). That import silently failed
(`platform/core/urls.py` mounts every app's urls optionally, swallowing
ModuleNotFoundError), taking down every `platform.provisioning` route in
the standalone project's own test suite with no error surfaced anywhere
except a 404 -- discovered while adding `platform.ephemeral_envs`, not
caused by it (confirmed via `git stash` against a clean checkout).
"""
from rest_framework import relations, serializers, viewsets

from platform.api.permissions import IsAuthenticatedViaClaims


def _is_tenant_model(model) -> bool:
    return any(f.name == "tenant_id" for f in model._meta.get_fields())


def scope_related_fields(serializer, tenant_id) -> None:
    """Restrict every writable related-field queryset in `serializer`
    (recursing into nested / many=True child serializers) to rows of
    `tenant_id`. DRF's default PrimaryKeyRelatedField queryset is
    `Model.objects.all()`, so without this a caller could POST another
    tenant's row id and have it attached to their own record."""
    if isinstance(serializer, serializers.ListSerializer):
        scope_related_fields(serializer.child, tenant_id)
        return
    if not isinstance(serializer, serializers.Serializer):
        return
    for field in serializer.fields.values():
        if isinstance(field, relations.ManyRelatedField):
            field = field.child_relation
        if isinstance(field, relations.RelatedField):
            qs = getattr(field, "queryset", None)
            if qs is not None and not field.read_only and _is_tenant_model(qs.model):
                field.queryset = qs.filter(tenant_id=tenant_id)
        elif isinstance(field, (serializers.Serializer, serializers.ListSerializer)):
            scope_related_fields(field, tenant_id)


class TenantScopedModelViewSet(viewsets.ModelViewSet):
    """No DB-level RLS policies exist for every table yet, so tenant
    isolation is enforced here at the queryset level.
    `request.tenant_id` is set by the active tenant-isolation middleware
    (None only for platform_admin cross-tenant use)."""

    permission_classes = [IsAuthenticatedViaClaims]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is None:
            return qs
        return qs.filter(tenant_id=tenant_id)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is not None and self.request.method not in ("GET", "HEAD", "OPTIONS"):
            scope_related_fields(serializer, tenant_id)
        return serializer

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)
