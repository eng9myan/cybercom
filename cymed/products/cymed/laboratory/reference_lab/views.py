from platform.canonical import events as canonical_events

from ..views import LaboratoryModelViewSet
from .models import ReferenceLab, ReferenceLabOrder, ReferenceLabResult, ReferenceLabRouting
from .serializers import (
    ReferenceLabOrderSerializer,
    ReferenceLabResultSerializer,
    ReferenceLabRoutingSerializer,
    ReferenceLabSerializer,
)


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
        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        canonical_events.emit(
            event_type="cymed.lab.reference.sent",
            aggregate_type="ReferenceLabOrder",
            aggregate_id=obj.id,
            tenant_id=tenant_id,
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
        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        canonical_events.emit(
            event_type="cymed.lab.reference.received",
            aggregate_type="ReferenceLabResult",
            aggregate_id=obj.id,
            tenant_id=tenant_id,
            payload={"result_id": str(obj.id), "status": obj.status},
        )
