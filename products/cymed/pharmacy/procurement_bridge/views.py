"""CyMed Pharmacy — Procurement Bridge Views."""
import uuid
from rest_framework.decorators import action
from rest_framework.response import Response
from platform.events.models import OutboxEvent
from .models import ProcurementRequest
from .serializers import ProcurementRequestSerializer
from ..views import PharmacyModelViewSet


class ProcurementRequestViewSet(PharmacyModelViewSet):
    queryset = ProcurementRequest.objects.all()
    serializer_class = ProcurementRequestSerializer
    required_feature = "pharmacy.procurement"
    filterset_fields = ["request_type", "status", "urgency"]
    search_fields = ["request_number", "drug_name", "drug_code"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        req_number = f"PRQ-{str(uuid.uuid4()).upper()[:12]}"
        obj = serializer.save(tenant_id=tenant_id, request_number=req_number)
        # Notify CyCom ERP via event bus
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.procurement.requested",
            event_type="cymed.procurement.requested",
            payload={
                "request_id": str(obj.id),
                "request_number": obj.request_number,
                "drug_code": obj.drug_code,
                "quantity": str(obj.quantity_requested),
                "urgency": obj.urgency,
            },
        )

    @action(detail=True, methods=["post"], url_path="submit-to-erp")
    def submit_to_erp(self, request, pk=None):
        """Submit procurement request to CyCom ERP via CyIntegrationHub."""
        import django.utils.timezone as tz
        req = self.get_object()
        tenant_id = getattr(request, "tenant_id", None)

        try:
            from platform.cyintegrationhub.services import IntegrationHubService
            result = IntegrationHubService.submit_procurement_request(
                request_id=str(req.id), tenant_id=str(tenant_id)
            )
            req.status = "submitted"
            req.erp_submitted_at = tz.now()
            req.erp_response = result
            req.save(update_fields=["status", "erp_submitted_at", "erp_response"])
        except Exception as e:
            return Response({"detail": f"ERP submission failed: {str(e)}"}, status=503)

        return Response(ProcurementRequestSerializer(req).data)
