from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Asset, AssetDepreciation
from .serializers import AssetDepreciationSerializer, AssetSerializer


class BaseAssetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        return self.queryset.filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class AssetViewSet(BaseAssetViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer


class AssetDepreciationViewSet(BaseAssetViewSet):
    queryset = AssetDepreciation.objects.all()
    serializer_class = AssetDepreciationSerializer
