"""
CyMed Population Health — Quality ViewSets
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import QualityMeasure, QualityMeasureResult, QualityImprovement, ClinicalAudit
from .serializers import (
    QualityMeasureSerializer,
    QualityMeasureResultSerializer,
    QualityImprovementSerializer,
    ClinicalAuditSerializer,
)


class PopulationHealthModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class QualityMeasureViewSet(PopulationHealthModelViewSet):
    queryset = QualityMeasure.objects.all()
    serializer_class = QualityMeasureSerializer
    filterset_fields = ["measure_type", "is_national", "is_active", "reporting_period"]
    search_fields = ["measure_code", "measure_name"]


class QualityMeasureResultViewSet(PopulationHealthModelViewSet):
    queryset = QualityMeasureResult.objects.select_related("measure")
    serializer_class = QualityMeasureResultSerializer
    filterset_fields = ["measure", "facility_id", "meets_target", "period_start"]


class QualityImprovementViewSet(PopulationHealthModelViewSet):
    queryset = QualityImprovement.objects.select_related("measure_result")
    serializer_class = QualityImprovementSerializer
    filterset_fields = ["measure_result", "status", "intervention_type"]


class ClinicalAuditViewSet(PopulationHealthModelViewSet):
    queryset = ClinicalAudit.objects.all()
    serializer_class = ClinicalAuditSerializer
    filterset_fields = ["facility_id", "audit_type", "status"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        audit = self.get_object()
        audit.status = "completed"
        # Recalculate compliance rate if sample_size is set
        if audit.sample_size > 0:
            audit.compliance_rate = round(
                (audit.compliant_count / audit.sample_size) * 100, 2
            )
        audit.save(update_fields=["status", "compliance_rate", "updated_at"])
        return Response(ClinicalAuditSerializer(audit).data)
