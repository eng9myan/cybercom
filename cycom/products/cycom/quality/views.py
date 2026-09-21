from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.quality.models import (
    CheckpointCriterionResult,
    InspectionPlan,
    NonConformance,
    QualityCheckpoint,
)
from products.cycom.quality.serializers import (
    CheckpointCriterionResultSerializer,
    InspectionPlanSerializer,
    NonConformanceSerializer,
    QualityCheckpointSerializer,
)
from products.cycom.quality.services import record_result


class InspectionPlanViewSet(TenantScopedModelViewSet):
    queryset = InspectionPlan.objects.prefetch_related("criteria").all()
    serializer_class = InspectionPlanSerializer
    filterset_fields = ["is_active", "linked_model"]


class QualityCheckpointViewSet(TenantScopedModelViewSet):
    queryset = QualityCheckpoint.objects.select_related("inspection_plan").prefetch_related(
        "criterion_results", "non_conformances"
    ).all()
    serializer_class = QualityCheckpointSerializer

    @action(detail=True, methods=["post"], url_path="record-result")
    def record(self, request, pk=None):
        checkpoint = self.get_object()
        result = request.data.get("result")
        if not result:
            raise ValidationError("result is required.")
        claims = getattr(request, "auth_claims", {}) or {}
        checked_by = request.data.get("checked_by", "") or claims.get("email", "")
        record_result(checkpoint, result=result, checked_by=checked_by, notes=request.data.get("notes", ""))
        # record_result may have created a NonConformance via a separate
        # query — checkpoint's prefetched non_conformances cache (from
        # self.get_object()) predates that insert, so re-fetch instead of
        # serializing the stale in-memory instance.
        checkpoint = self.get_queryset().get(pk=checkpoint.pk)
        return Response(QualityCheckpointSerializer(checkpoint).data)


class CheckpointCriterionResultViewSet(TenantScopedModelViewSet):
    queryset = CheckpointCriterionResult.objects.select_related("criterion", "checkpoint").all()
    serializer_class = CheckpointCriterionResultSerializer
    filterset_fields = ["checkpoint"]


class NonConformanceViewSet(TenantScopedModelViewSet):
    queryset = NonConformance.objects.select_related("checkpoint").all()
    serializer_class = NonConformanceSerializer
    filterset_fields = ["status", "checkpoint"]

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        ncr = self.get_object()
        if ncr.status == "closed":
            raise ValidationError("Already closed.")
        if not ncr.disposition:
            raise ValidationError("A disposition is required before closing a non-conformance.")
        if not ncr.corrective_action:
            raise ValidationError("A corrective action is required before closing a non-conformance.")
        ncr.status = "closed"
        ncr.closed_at = timezone.now()
        ncr.save(update_fields=["status", "closed_at", "updated_at"])
        return Response(NonConformanceSerializer(ncr).data)
