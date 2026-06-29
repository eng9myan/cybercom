import uuid

from platform.events.models import OutboxEvent

from ..views import LaboratoryModelViewSet
from .models import (
    LabOrder,
    LabOrderAttachment,
    LabOrderDiagnosis,
    LabOrderItem,
    LabPanel,
    LabTest,
)
from .serializers import (
    LabOrderAttachmentSerializer,
    LabOrderDiagnosisSerializer,
    LabOrderItemSerializer,
    LabOrderSerializer,
    LabPanelSerializer,
    LabTestSerializer,
)


class LabTestViewSet(LaboratoryModelViewSet):
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer
    required_feature = "lab.orders"
    filterset_fields = ["category", "department", "is_active"]
    search_fields = ["code", "name", "loinc_code"]


class LabPanelViewSet(LaboratoryModelViewSet):
    queryset = LabPanel.objects.prefetch_related("tests")
    serializer_class = LabPanelSerializer
    required_feature = "lab.orders"
    filterset_fields = ["category", "is_active", "is_orderable"]


class LabOrderViewSet(LaboratoryModelViewSet):
    queryset = LabOrder.objects.prefetch_related("items", "diagnoses").select_related()
    serializer_class = LabOrderSerializer
    required_feature = "lab.orders"
    filterset_fields = ["order_type", "priority", "status"]
    search_fields = ["order_number", "hl7_placer_order_number"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        order_number = f"LAB-{str(uuid.uuid4()).upper()[:12]}"
        obj = serializer.save(tenant_id=tenant_id, order_number=order_number)
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.lab.order.created",
            event_type="cymed.lab.order.created",
            payload={
                "order_id": str(obj.id),
                "order_number": obj.order_number,
                "priority": obj.priority,
            },
        )


class LabOrderItemViewSet(LaboratoryModelViewSet):
    queryset = LabOrderItem.objects.select_related("order", "test", "panel")
    serializer_class = LabOrderItemSerializer
    required_feature = "lab.orders"
    filterset_fields = ["order", "status", "priority"]


class LabOrderDiagnosisViewSet(LaboratoryModelViewSet):
    queryset = LabOrderDiagnosis.objects.all()
    serializer_class = LabOrderDiagnosisSerializer
    required_feature = "lab.orders"


class LabOrderAttachmentViewSet(LaboratoryModelViewSet):
    queryset = LabOrderAttachment.objects.all()
    serializer_class = LabOrderAttachmentSerializer
    required_feature = "lab.orders"
