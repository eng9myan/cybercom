from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import CensusDataPoint, StaffingForecast, ForecastAdjustment, ForecastRosterMapping
from .serializers import (
    CensusDataPointSerializer,
    StaffingForecastSerializer,
    ForecastAdjustmentSerializer,
    ForecastRosterMappingSerializer,
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


class CensusDataPointViewSet(HWMModelViewSet):
    queryset = CensusDataPoint.objects.all()
    serializer_class = CensusDataPointSerializer
    filterset_fields = ["facility_id", "department_id", "census_date", "source"]
    ordering_fields = ["census_date", "actual_census", "created_at"]


class StaffingForecastViewSet(HWMModelViewSet):
    queryset = StaffingForecast.objects.all()
    serializer_class = StaffingForecastSerializer
    filterset_fields = ["facility_id", "department_id", "forecast_date", "status", "surge_predicted"]
    ordering_fields = ["forecast_date", "generated_at", "created_at"]

    @action(detail=True, methods=["get"])
    def adjustments(self, request, pk=None):
        forecast = self.get_object()
        qs = forecast.adjustments.all()
        serializer = ForecastAdjustmentSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def roster_mappings(self, request, pk=None):
        forecast = self.get_object()
        qs = forecast.roster_mappings.all()
        serializer = ForecastRosterMappingSerializer(qs, many=True)
        return Response(serializer.data)


class ForecastAdjustmentViewSet(HWMModelViewSet):
    queryset = ForecastAdjustment.objects.select_related("forecast")
    serializer_class = ForecastAdjustmentSerializer
    filterset_fields = ["forecast", "adjusted_by_id"]
    ordering_fields = ["created_at"]


class ForecastRosterMappingViewSet(HWMModelViewSet):
    queryset = ForecastRosterMapping.objects.select_related("forecast")
    serializer_class = ForecastRosterMappingSerializer
    filterset_fields = ["forecast", "roster_cycle_id"]
    ordering_fields = ["applied_at", "created_at"]
    http_method_names = ["get", "post", "head", "options"]
