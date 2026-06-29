from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import StockItem, StockMovement, Warehouse
from .serializers import StockItemSerializer, StockMovementSerializer, WarehouseSerializer


class BaseInventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        return self.queryset.filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class WarehouseViewSet(BaseInventoryViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class StockItemViewSet(BaseInventoryViewSet):
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer


class StockMovementViewSet(BaseInventoryViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
