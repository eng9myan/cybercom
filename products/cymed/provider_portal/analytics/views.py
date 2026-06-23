from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    ProviderProductivitySnapshot,
    ClinicalQualityMetric,
    WorkforceDashboardSnapshot,
    ProviderAIInsight,
    ExecutiveDashboardMetric,
)
from .serializers import (
    ProviderProductivitySnapshotSerializer,
    ClinicalQualityMetricSerializer,
    WorkforceDashboardSnapshotSerializer,
    ProviderAIInsightSerializer,
    ExecutiveDashboardMetricSerializer,
)


class ProviderProductivitySnapshotViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderProductivitySnapshotSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "provider_id",
        "snapshot_date",
        "snapshot_period",
        "provider_type",
    ]
    search_fields = ["provider_name", "provider_type"]
    ordering_fields = ["snapshot_date", "patients_seen", "notes_completed", "created_at"]
    ordering = ["-snapshot_date"]

    def get_queryset(self):
        return ProviderProductivitySnapshot.objects.filter(
            tenant_id=self.request.tenant_id
        )


class ClinicalQualityMetricViewSet(viewsets.ModelViewSet):
    serializer_class = ClinicalQualityMetricSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "metric_type",
        "scope_type",
        "scope_id",
        "measured_at",
        "meets_target",
    ]
    search_fields = ["metric_name", "scope_name", "notes"]
    ordering_fields = ["measured_at", "rate", "target_rate", "created_at"]
    ordering = ["-measured_at"]

    def get_queryset(self):
        return ClinicalQualityMetric.objects.filter(
            tenant_id=self.request.tenant_id
        )


class WorkforceDashboardSnapshotViewSet(viewsets.ModelViewSet):
    serializer_class = WorkforceDashboardSnapshotSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["unit_id", "snapshot_date", "department"]
    search_fields = ["unit_name", "department"]
    ordering_fields = ["snapshot_date", "total_providers", "patient_census", "created_at"]
    ordering = ["-snapshot_date"]

    def get_queryset(self):
        return WorkforceDashboardSnapshot.objects.filter(
            tenant_id=self.request.tenant_id
        )


class ProviderAIInsightViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderAIInsightSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "provider_id",
        "patient_id",
        "insight_type",
        "status",
        "is_advisory_only",
    ]
    search_fields = ["insight_title", "insight_body", "action_taken"]
    ordering_fields = ["created_at", "confidence_score", "acknowledged_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return ProviderAIInsight.objects.filter(
            tenant_id=self.request.tenant_id
        )


class ExecutiveDashboardMetricViewSet(viewsets.ModelViewSet):
    serializer_class = ExecutiveDashboardMetricSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "metric_category",
        "metric_date",
        "facility_id",
        "trend_direction",
        "is_above_threshold",
    ]
    search_fields = ["metric_name", "department", "metric_unit"]
    ordering_fields = ["metric_date", "metric_value", "created_at"]
    ordering = ["-metric_date"]

    def get_queryset(self):
        return ExecutiveDashboardMetric.objects.filter(
            tenant_id=self.request.tenant_id
        )
