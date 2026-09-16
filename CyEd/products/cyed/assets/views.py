from core.viewsets import TenantScopedModelViewSet
from products.cyed.assets.models import Asset
from products.cyed.assets.serializers import AssetSerializer
from products.cyed.governance.access import IsStaff


class AssetViewSet(TenantScopedModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        return qs.filter(category__iexact=category) if category else qs
