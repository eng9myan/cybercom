from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated


class CommercialModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all CyMed Commercial module endpoints.
    Enforces authentication. Commercial endpoints operate at the
    platform-admin level, not per-tenant, so no tenant_id filtering
    is applied by default — but subclasses can override get_queryset()
    to scope by customer_id or tenant_id as appropriate.
    """
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Inject tenant_id from JWT into new records where applicable."""
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id and hasattr(serializer.Meta.model, "tenant_id"):
            serializer.save(tenant_id=tenant_id)
        else:
            serializer.save()
