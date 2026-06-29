from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from products.cymed.core.providers.models import Provider
from products.cymed.core.providers.serializers import ProviderSerializer


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.filter(is_deleted=False)
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
