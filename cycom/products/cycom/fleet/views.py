from core.viewsets import TenantScopedModelViewSet
from products.cycom.fleet.models import FuelLog, MaintenanceLog, Vehicle
from products.cycom.fleet.serializers import (
    FuelLogSerializer,
    MaintenanceLogSerializer,
    VehicleSerializer,
)


class VehicleViewSet(TenantScopedModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    filterset_fields = ["status"]


class MaintenanceLogViewSet(TenantScopedModelViewSet):
    queryset = MaintenanceLog.objects.select_related("vehicle").all()
    serializer_class = MaintenanceLogSerializer
    filterset_fields = ["vehicle"]


class FuelLogViewSet(TenantScopedModelViewSet):
    queryset = FuelLog.objects.select_related("vehicle").all()
    serializer_class = FuelLogSerializer
    filterset_fields = ["vehicle"]
