from core.viewsets import TenantScopedModelViewSet
from products.cycom.planning.models import ShiftSlot
from products.cycom.planning.serializers import ShiftSlotSerializer


class ShiftSlotViewSet(TenantScopedModelViewSet):
    queryset = ShiftSlot.objects.all()
    serializer_class = ShiftSlotSerializer
