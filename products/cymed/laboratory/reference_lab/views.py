from platform.events.models import OutboxEvent
from .models import ReferenceLab, ReferenceLabRouting, ReferenceLabOrder, ReferenceLabResult
from .serializers import ReferenceLabSerializer, ReferenceLabRoutingSerializer, ReferenceLabOrderSerializer, ReferenceLabResultSerializer
from ..views import LaboratoryModelViewSet

class ReferenceLabViewSet(LaboratoryModelViewSet):
    queryset = ReferenceLab.objects.all()
    serializer_class = ReferenceLabSerializer
    required_feature = "lab.reference_lab"
    filterset_fields = ["status", "integration_type", "is_national", "is_government"]
    search_fields = ["code", "name"]

class ReferenceLabRoutingViewSet(LaboratoryModelViewSet):
    queryset = ReferenceLabRouting.objects.select_related("test", "reference_lab")
    serializer_class = ReferenceLabRoutingSerializer
    required_feature = "lab.reference_lab"
    filterset_fields = ["test", "reference_lab", "is_active", "is_default"]

class ReferenceLabOrderViewSet(LaboratoryModelViewSet):
    queryset = ReferenceLabOrder.objects.select_related("reference_lab")
    serializer_class = ReferenceLabOrderSerializer
    required_feature = "lab.reference_lab"
    filterset_fields = ["reference_lab", "status"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(tenant_id=tenant_id)
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.lab.reference.sent",
            event_type="cymed.lab.reference.sent",
            payload={"reference_order_id": str(obj.id), "reference_lab": obj.reference_lab.code},
        )

class ReferenceLabResultViewSet(LaboratoryModelViewSet):
    queryset = ReferenceLabResult.objects.all()
    serializer_class = ReferenceLabResultSerializer
    required_feature = "lab.reference_lab"
    filterset_fields = ["status"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(tenant_id=tenant_id)
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.lab.reference.received",
            event_type="cymed.lab.reference.received",
            payload={"result_id": str(obj.id), "status": obj.status},
        )
