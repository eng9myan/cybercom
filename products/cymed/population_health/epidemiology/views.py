from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import EpidemiologyStudy, DiseaseTrend, PopulationIndicator, HealthMeasure
from .serializers import (
    EpidemiologyStudySerializer,
    DiseaseTrendSerializer,
    PopulationIndicatorSerializer,
    HealthMeasureSerializer,
)


class EpidemiologyBaseViewSet(viewsets.ModelViewSet):
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


class EpidemiologyStudyViewSet(EpidemiologyBaseViewSet):
    queryset = EpidemiologyStudy.objects.all()
    serializer_class = EpidemiologyStudySerializer
    filterset_fields = ["study_type", "status", "disease_code"]
    search_fields = ["study_name"]
    ordering_fields = ["study_name", "start_date", "created_at"]


class DiseaseTrendViewSet(EpidemiologyBaseViewSet):
    queryset = DiseaseTrend.objects.all()
    serializer_class = DiseaseTrendSerializer
    filterset_fields = ["disease_code", "period_type", "period_date", "geographic_scope"]
    search_fields = ["disease_name", "disease_code"]
    ordering_fields = ["period_date", "disease_code", "created_at"]


class PopulationIndicatorViewSet(EpidemiologyBaseViewSet):
    queryset = PopulationIndicator.objects.all()
    serializer_class = PopulationIndicatorSerializer
    filterset_fields = ["indicator_type", "geographic_scope", "gender"]
    search_fields = ["indicator_code", "indicator_name"]
    ordering_fields = ["indicator_code", "measurement_date", "created_at"]


class HealthMeasureViewSet(EpidemiologyBaseViewSet):
    queryset = HealthMeasure.objects.all()
    serializer_class = HealthMeasureSerializer
    filterset_fields = ["measure_type", "period_year", "geographic_scope", "gender"]
    search_fields = ["measure_name"]
    ordering_fields = ["measure_name", "period_year", "created_at"]
