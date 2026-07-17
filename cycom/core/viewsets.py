from rest_framework import viewsets

from core.permissions import IsAuthenticatedViaClaims


class TenantScopedModelViewSet(viewsets.ModelViewSet):
    """
    No DB-level RLS policies exist anywhere yet, so tenant isolation is
    enforced here at the queryset level. request.tenant_id is set by
    TenantIsolationMiddleware (None only for platform_admin cross-tenant use).
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is None:
            return qs
        return qs.filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id)
