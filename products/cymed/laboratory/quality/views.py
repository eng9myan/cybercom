from decimal import Decimal, InvalidOperation
from platform.events.models import OutboxEvent
from .models import QualityRule, QualityControl, QualityRun, QualityFailure, ProficiencyTest
from .serializers import QualityRuleSerializer, QualityControlSerializer, QualityRunSerializer, QualityFailureSerializer, ProficiencyTestSerializer
from ..views import LaboratoryModelViewSet

class QualityRuleViewSet(LaboratoryModelViewSet):
    queryset = QualityRule.objects.all()
    serializer_class = QualityRuleSerializer
    required_feature = "lab.quality"
    filterset_fields = ["rule_type", "is_active", "is_rejection"]

class QualityControlViewSet(LaboratoryModelViewSet):
    queryset = QualityControl.objects.all()
    serializer_class = QualityControlSerializer
    required_feature = "lab.quality"
    filterset_fields = ["test", "level", "is_active"]

class QualityRunViewSet(LaboratoryModelViewSet):
    queryset = QualityRun.objects.select_related("qc")
    serializer_class = QualityRunSerializer
    required_feature = "lab.quality"
    filterset_fields = ["qc", "passed", "run_date"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        qc = serializer.validated_data["qc"]
        value = Decimal(str(serializer.validated_data["measured_value"]))
        mean = Decimal(str(qc.target_mean))
        sd = Decimal(str(qc.target_sd))
        z_score = (value - mean) / sd if sd != 0 else Decimal("0")
        sd_limit = Decimal(str(qc.allowable_sd_multiplier))
        is_warning = abs(z_score) > sd_limit
        is_rejection = abs(z_score) > sd_limit * Decimal("1.5")
        passed = not is_rejection
        rules_triggered = []
        if is_rejection:
            rules_triggered.append("13s")
        elif is_warning:
            rules_triggered.append("12s")
        obj = serializer.save(tenant_id=tenant_id, z_score=z_score, passed=passed, is_warning=is_warning, is_rejection=is_rejection, rules_triggered=rules_triggered)
        if is_rejection:
            QualityFailure.objects.create(tenant_id=tenant_id, qc_run=obj)
            OutboxEvent.objects.create(
                tenant_id=str(tenant_id) if tenant_id else None,
                topic="cymed.lab.qc.failed",
                event_type="cymed.lab.qc.failed",
                payload={"qc_run_id": str(obj.id), "z_score": str(z_score), "rules": rules_triggered},
            )

class QualityFailureViewSet(LaboratoryModelViewSet):
    queryset = QualityFailure.objects.all()
    serializer_class = QualityFailureSerializer
    required_feature = "lab.quality"
    filterset_fields = ["status", "patient_results_affected"]

class ProficiencyTestViewSet(LaboratoryModelViewSet):
    queryset = ProficiencyTest.objects.all()
    serializer_class = ProficiencyTestSerializer
    required_feature = "lab.quality"
    filterset_fields = ["status"]
