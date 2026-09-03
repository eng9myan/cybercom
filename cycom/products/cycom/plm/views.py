from core.viewsets import TenantScopedModelViewSet
from products.cycom.plm.models import BomComponent, EngineeringChangeOrder, ProductBOM
from products.cycom.plm.serializers import (
    BomComponentSerializer,
    EngineeringChangeOrderSerializer,
    ProductBOMSerializer,
)


class ProductBOMViewSet(TenantScopedModelViewSet):
    queryset = ProductBOM.objects.prefetch_related("components").all()
    serializer_class = ProductBOMSerializer


class BomComponentViewSet(TenantScopedModelViewSet):
    queryset = BomComponent.objects.all()
    serializer_class = BomComponentSerializer


class EngineeringChangeOrderViewSet(TenantScopedModelViewSet):
    queryset = EngineeringChangeOrder.objects.all()
    serializer_class = EngineeringChangeOrderSerializer
