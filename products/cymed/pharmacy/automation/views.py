"""CyMed Pharmacy — Automation Views."""
import django.utils.timezone as tz
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AutomationDevice, DispensingRobot, CabinetDevice, AutomationQueue
from .serializers import (
    AutomationDeviceSerializer, DispensingRobotSerializer,
    CabinetDeviceSerializer, AutomationQueueSerializer
)
from ..views import PharmacyModelViewSet


class AutomationDeviceViewSet(PharmacyModelViewSet):
    queryset = AutomationDevice.objects.select_related("robot_profile", "cabinet_profile")
    serializer_class = AutomationDeviceSerializer
    required_feature = "pharmacy.automation"
    filterset_fields = ["device_type", "status", "facility_id", "ward_id", "is_active"]
    search_fields = ["device_code", "device_name", "location"]

    @action(detail=True, methods=["post"], url_path="send-to-hub")
    def send_to_hub(self, request, pk=None):
        """
        Route a dispense request to this device via CyIntegrationHub.
        The Hub owns the actual device communication protocol.
        """
        device = self.get_object()
        dispense_data = request.data
        try:
            from platform.cyintegrationhub.services import IntegrationHubService
            response = IntegrationHubService.route_pharmacy_dispense(
                device_id=device.integration_hub_device_id,
                dispense_data=dispense_data,
            )
            return Response({"hub_response": response})
        except Exception as e:
            return Response({"detail": f"Hub routing failed: {str(e)}"}, status=503)

    @action(detail=True, methods=["post"], url_path="status-ping")
    def status_ping(self, request, pk=None):
        """Ping device status via CyIntegrationHub."""
        device = self.get_object()
        device.last_seen_at = tz.now()
        device.save(update_fields=["last_seen_at"])
        return Response({"device_id": str(device.id), "status": device.status, "last_seen": str(device.last_seen_at)})


class DispensingRobotViewSet(PharmacyModelViewSet):
    queryset = DispensingRobot.objects.select_related("device")
    serializer_class = DispensingRobotSerializer
    required_feature = "pharmacy.automation"


class CabinetDeviceViewSet(PharmacyModelViewSet):
    queryset = CabinetDevice.objects.select_related("device")
    serializer_class = CabinetDeviceSerializer
    required_feature = "pharmacy.automation"
    filterset_fields = ["cabinet_type", "requires_biometric", "requires_witness"]


class AutomationQueueViewSet(PharmacyModelViewSet):
    queryset = AutomationQueue.objects.select_related("device")
    serializer_class = AutomationQueueSerializer
    required_feature = "pharmacy.automation"
    filterset_fields = ["status", "priority", "device"]

    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        """Retry a failed automation queue item."""
        item = self.get_object()
        if item.status not in ("failed", "timeout"):
            return Response({"detail": "Only failed/timeout items can be retried."}, status=400)
        item.status = "pending"
        item.retry_count += 1
        item.failure_reason = ""
        item.save(update_fields=["status", "retry_count", "failure_reason"])
        return Response(AutomationQueueSerializer(item).data)

    @action(detail=True, methods=["post"], url_path="fallback-manual")
    def fallback_manual(self, request, pk=None):
        """Mark item for manual dispensing fallback."""
        item = self.get_object()
        item.fallback_to_manual = True
        item.status = "cancelled"
        item.save(update_fields=["fallback_to_manual", "status"])
        return Response({"detail": "Routed to manual dispensing.", "item_id": str(item.id)})
