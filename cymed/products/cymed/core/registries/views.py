from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from products.cymed.core.registries.models import CohortRegistry, RegistryEntry
from products.cymed.core.registries.serializers import (
    CohortRegistrySerializer,
    RegistryEntrySerializer,
)


class CohortRegistryViewSet(viewsets.ModelViewSet):
    queryset = CohortRegistry.objects.filter(is_active=True)
    serializer_class = CohortRegistrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class RegistryEntryViewSet(viewsets.ModelViewSet):
    queryset = RegistryEntry.objects.all()
    serializer_class = RegistryEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)
