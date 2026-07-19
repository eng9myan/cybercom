from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.maintenance.models import Equipment, MaintenanceRequest
from products.cycom.maintenance.serializers import EquipmentSerializer, MaintenanceRequestSerializer
from products.cycom.maintenance.services import complete_request, start_request


class EquipmentViewSet(TenantScopedModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer


class MaintenanceRequestViewSet(TenantScopedModelViewSet):
    queryset = MaintenanceRequest.objects.all()
    serializer_class = MaintenanceRequestSerializer

    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        req = start_request(self.get_object())
        return Response(MaintenanceRequestSerializer(req).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        req = complete_request(self.get_object())
        return Response(MaintenanceRequestSerializer(req).data)
