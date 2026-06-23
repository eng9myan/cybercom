"""CyMed Pharmacy — Inventory Bridge Views."""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from platform.events.models import OutboxEvent
from .models import MedicationConsumptionEvent, InventoryQueryResult
from .serializers import MedicationConsumptionEventSerializer, InventoryQueryResultSerializer
from ..views import PharmacyModelViewSet


class MedicationConsumptionEventViewSet(PharmacyModelViewSet):
    queryset = MedicationConsumptionEvent.objects.all()
    serializer_class = MedicationConsumptionEventSerializer
    required_feature = "pharmacy.inventory"
    filterset_fields = ["erp_sync_status", "drug_code"]
    ordering = ["-dispensed_at"]

    @action(detail=True, methods=["post"], url_path="retry-erp-sync")
    def retry_erp_sync(self, request, pk=None):
        """Manually retry ERP sync for a failed consumption event."""
        event = self.get_object()
        tenant_id = getattr(request, "tenant_id", None)
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.inventory.consumed",
            event_type="cymed.inventory.consumed.retry",
            payload={
                "consumption_id": str(event.id),
                "drug_code": event.drug_code,
                "quantity": str(event.quantity),
                "dispense_order_id": str(event.dispense_order_id),
            },
        )
        event.erp_sync_status = "pending"
        event.erp_error = ""
        event.save(update_fields=["erp_sync_status", "erp_error"])
        return Response({"status": "retry_queued"})


class InventoryQueryView(APIView):
    """
    Query current inventory status from CyCom ERP via CyIntegrationHub.
    Results are cached in InventoryQueryResult for performance.
    CyCom owns the actual inventory — this is read-only bridge.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        drug_code = request.query_params.get("drug_code")
        if not drug_code:
            return Response({"detail": "drug_code query parameter required."}, status=400)

        tenant_id = getattr(request, "tenant_id", None)
        cached = InventoryQueryResult.objects.filter(
            tenant_id=tenant_id, drug_code=drug_code
        ).first()

        if cached:
            return Response(InventoryQueryResultSerializer(cached).data)

        # Query CyCom ERP via CyIntegrationHub
        try:
            from platform.cyintegrationhub.services import IntegrationHubService
            erp_data = IntegrationHubService.query_erp_inventory(
                drug_code=drug_code, tenant_id=str(tenant_id)
            )
            result = InventoryQueryResult.objects.create(
                tenant_id=tenant_id,
                drug_code=drug_code,
                **erp_data,
            )
            return Response(InventoryQueryResultSerializer(result).data)
        except Exception as e:
            return Response({"detail": f"ERP query failed: {str(e)}", "drug_code": drug_code}, status=503)
