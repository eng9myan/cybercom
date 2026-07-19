from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.manufacturing.models import BillOfMaterial, BOMComponent, ManufacturingOrder
from products.cycom.manufacturing.serializers import (
    BillOfMaterialSerializer,
    BOMComponentSerializer,
    ManufacturingOrderSerializer,
)
from products.cycom.manufacturing.services import complete_manufacturing_order


class BillOfMaterialViewSet(TenantScopedModelViewSet):
    queryset = BillOfMaterial.objects.all()
    serializer_class = BillOfMaterialSerializer


class BOMComponentViewSet(TenantScopedModelViewSet):
    queryset = BOMComponent.objects.all()
    serializer_class = BOMComponentSerializer


class ManufacturingOrderViewSet(TenantScopedModelViewSet):
    queryset = ManufacturingOrder.objects.all()
    serializer_class = ManufacturingOrderSerializer

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        mo = self.get_object()
        complete_manufacturing_order(mo)
        return Response(ManufacturingOrderSerializer(mo).data)
