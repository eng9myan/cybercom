"""
CyMed Population Health — Analytics Views
"""

import django.utils.timezone as timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    NationalHealthSnapshot,
    OutbreakForecast,
    PopulationAnalyticsInsight,
    PopulationHealthDashboard,
    QualityKPIDashboard,
)
from .serializers import (
    NationalHealthSnapshotSerializer,
    OutbreakForecastSerializer,
    PopulationAnalyticsInsightSerializer,
    PopulationHealthDashboardSerializer,
    QualityKPIDashboardSerializer,
)


class PopulationHealthModelViewSet(viewsets.ModelViewSet):
    """Base ViewSet that scopes all queries to the current tenant."""

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


class NationalHealthSnapshotViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only + create viewset for national health snapshots."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = NationalHealthSnapshot.objects.all()
    serializer_class = NationalHealthSnapshotSerializer
    filterset_fields = ["snapshot_date", "period_type", "geographic_scope"]
    ordering_fields = ["snapshot_date", "created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class PopulationAnalyticsInsightViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only viewset for analytics insights with acknowledge action."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = PopulationAnalyticsInsight.objects.all()
    serializer_class = PopulationAnalyticsInsightSerializer
    filterset_fields = ["insight_type", "scope_type", "status", "is_ai_generated"]
    ordering_fields = ["created_at", "status"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        insight = self.get_object()
        if insight.status not in ("pending_review",):
            return Response(
                {"detail": "Insight has already been acknowledged or is not pending review."},
                status=400,
            )
        user_id = getattr(request.user, "id", None)
        insight.status = "acknowledged"
        insight.acknowledged_by_user_id = user_id
        insight.acknowledged_at = timezone.now()
        insight.save(
            update_fields=["status", "acknowledged_by_user_id", "acknowledged_at", "updated_at"]
        )
        serializer = self.get_serializer(insight)
        return Response(serializer.data)


class QualityKPIDashboardViewSet(PopulationHealthModelViewSet):
    """Full CRUD for quality KPI dashboard entries."""

    queryset = QualityKPIDashboard.objects.all()
    serializer_class = QualityKPIDashboardSerializer
    filterset_fields = ["kpi_category", "facility_id", "meets_target", "trend_direction"]
    search_fields = ["kpi_name"]
    ordering_fields = ["kpi_name", "period_start", "period_end", "created_at"]


class OutbreakForecastViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only viewset for outbreak forecasts."""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    queryset = OutbreakForecast.objects.all()
    serializer_class = OutbreakForecastSerializer
    filterset_fields = ["disease_code", "risk_level", "forecast_date", "is_ai_generated"]
    ordering_fields = ["forecast_date", "risk_level", "created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class PopulationHealthDashboardViewSet(PopulationHealthModelViewSet):
    """Full CRUD for population health dashboards."""

    queryset = PopulationHealthDashboard.objects.all()
    serializer_class = PopulationHealthDashboardSerializer
    filterset_fields = ["dashboard_type", "facility_id"]
    ordering_fields = ["dashboard_name", "as_of_date", "created_at"]
