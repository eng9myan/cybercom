from django.utils import timezone
from platform.events.models import OutboxEvent
from .models import LabResult, ResultValue, ReferenceRange, ResultInterpretation, CriticalResult, ResultCorrection, ResultApproval
from .serializers import LabResultSerializer, ResultValueSerializer, ReferenceRangeSerializer, ResultInterpretationSerializer, CriticalResultSerializer, ResultCorrectionSerializer, ResultApprovalSerializer
from ..views import LaboratoryModelViewSet

class LabResultViewSet(LaboratoryModelViewSet):
    queryset = LabResult.objects.prefetch_related("values")
    serializer_class = LabResultSerializer
    required_feature = "lab.results"
    filterset_fields = ["status", "has_critical_value", "has_abnormal_value"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(tenant_id=tenant_id)
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.lab.result.created",
            event_type="cymed.lab.result.created",
            payload={"result_id": str(obj.id), "status": obj.status},
        )

class ResultValueViewSet(LaboratoryModelViewSet):
    queryset = ResultValue.objects.all()
    serializer_class = ResultValueSerializer
    required_feature = "lab.results"
    filterset_fields = ["result", "is_critical", "is_abnormal", "interpretation"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        obj = serializer.save(tenant_id=tenant_id)
        if obj.is_critical:
            CriticalResult.objects.get_or_create(
                result_value=obj,
                defaults={"tenant_id": tenant_id}
            )
            OutboxEvent.objects.create(
                tenant_id=str(tenant_id) if tenant_id else None,
                topic="cymed.lab.critical_result.created",
                event_type="cymed.lab.critical_result.created",
                payload={"result_value_id": str(obj.id), "analyte": obj.analyte_name, "value": str(obj.value_numeric or obj.value_text)},
            )

class ReferenceRangeViewSet(LaboratoryModelViewSet):
    queryset = ReferenceRange.objects.all()
    serializer_class = ReferenceRangeSerializer
    required_feature = "lab.results"
    filterset_fields = ["test", "sex", "is_active"]

class CriticalResultViewSet(LaboratoryModelViewSet):
    queryset = CriticalResult.objects.all()
    serializer_class = CriticalResultSerializer
    required_feature = "lab.results"
    filterset_fields = ["notification_status"]

class ResultCorrectionViewSet(LaboratoryModelViewSet):
    queryset = ResultCorrection.objects.all()
    serializer_class = ResultCorrectionSerializer
    required_feature = "lab.results"

class ResultApprovalViewSet(LaboratoryModelViewSet):
    queryset = ResultApproval.objects.all()
    serializer_class = ResultApprovalSerializer
    required_feature = "lab.results"

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        ip = self.request.META.get("REMOTE_ADDR", "")
        obj = serializer.save(tenant_id=tenant_id, ip_address=ip)
        result = obj.result
        if obj.approval_level == "pathologist":
            result.status = "approved"
            result.approved_by = obj.approved_by
            result.approved_at = obj.approved_at
            result.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
            OutboxEvent.objects.create(
                tenant_id=str(tenant_id) if tenant_id else None,
                topic="cymed.lab.result.verified",
                event_type="cymed.lab.result.verified",
                payload={"result_id": str(result.id), "approved_by": str(obj.approved_by)},
            )
