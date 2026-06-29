from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from .models import OnCallSLAMetric, WorkforceAnalyticsSnapshot, WorkforceReport
from .serializers import (
    OnCallSLAMetricSerializer,
    WorkforceAnalyticsSnapshotSerializer,
    WorkforceReportSerializer,
)


class HWMModelViewSet(viewsets.ModelViewSet):
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


class WorkforceAnalyticsSnapshotViewSet(HWMModelViewSet):
    queryset = WorkforceAnalyticsSnapshot.objects.all()
    serializer_class = WorkforceAnalyticsSnapshotSerializer
    filterset_fields = ["facility_id", "department_id", "period_type", "period_start"]
    ordering_fields = ["period_start", "coverage_compliance_pct", "vacancy_rate_pct", "created_at"]
    http_method_names = ["get", "post", "head", "options"]


class WorkforceReportViewSet(HWMModelViewSet):
    queryset = WorkforceReport.objects.all()
    serializer_class = WorkforceReportSerializer
    filterset_fields = ["report_type", "facility_id", "department_id", "generated_by_id"]
    ordering_fields = ["generated_at", "period_start", "created_at"]
    http_method_names = ["get", "post", "head", "options"]


class OnCallSLAMetricViewSet(HWMModelViewSet):
    queryset = OnCallSLAMetric.objects.all()
    serializer_class = OnCallSLAMetricSerializer
    filterset_fields = ["facility_id", "specialty", "metric_date"]
    ordering_fields = ["metric_date", "sla_compliance_pct", "created_at"]
    http_method_names = ["get", "post", "head", "options"]
