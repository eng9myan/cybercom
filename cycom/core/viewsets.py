from rest_framework import relations, serializers, viewsets

from core.permissions import IsAuthenticatedViaClaims


def _is_tenant_model(model) -> bool:
    return any(f.name == "tenant_id" for f in model._meta.get_fields())


def scope_related_fields(serializer, tenant_id) -> None:
    """Restrict every writable related-field queryset in `serializer`
    (recursing into nested / many=True child serializers, e.g. invoice
    lines) to rows of `tenant_id`.

    DRF's default PrimaryKeyRelatedField queryset is `Model.objects.all()`,
    so without this a caller could POST another tenant's account / partner /
    product id and have it attached to their own record: the object lookup
    was tenant-scoped, the FK targets weren't. Scoping the queryset makes
    such an id fail validation exactly like a non-existent one ("Invalid pk
    - object does not exist"), without revealing that it exists elsewhere.
    Models without a tenant_id column (global reference data) are untouched.
    """
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
    """
    No DB-level RLS policies exist anywhere yet, so tenant isolation is
    enforced here at the queryset level. request.tenant_id is set by
    TenantIsolationMiddleware (None only for platform_admin cross-tenant use).
    Writable foreign keys are scoped the same way (see scope_related_fields).
    """

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
