"""
CyMed Population Health — Care Gaps ViewSets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import CareGap, CareGapRule, CareGapRecommendation, CareGapResolution
from .serializers import (
    CareGapSerializer,
    CareGapRuleSerializer,
    CareGapRecommendationSerializer,
    CareGapResolutionSerializer,
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


class CareGapViewSet(PopulationHealthModelViewSet):
    queryset = CareGap.objects.all()
    serializer_class = CareGapSerializer
    filterset_fields = ["patient_id", "gap_type", "status", "priority", "due_date"]

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        gap = self.get_object()
        gap.status = "closed"
        gap.save(update_fields=["status", "updated_at"])
        return Response(CareGapSerializer(gap).data)

    @action(detail=True, methods=["post"])
    def waive(self, request, pk=None):
        gap = self.get_object()
        gap.status = "waived"
        gap.save(update_fields=["status", "updated_at"])
        return Response(CareGapSerializer(gap).data)


class CareGapRuleViewSet(PopulationHealthModelViewSet):
    queryset = CareGapRule.objects.all()
    serializer_class = CareGapRuleSerializer
    filterset_fields = ["gap_type", "is_active", "applies_to_gender"]
    search_fields = ["rule_name"]


class CareGapRecommendationViewSet(PopulationHealthModelViewSet):
    queryset = CareGapRecommendation.objects.select_related("care_gap")
    serializer_class = CareGapRecommendationSerializer
    filterset_fields = ["care_gap", "is_ai_generated"]


class CareGapResolutionViewSet(PopulationHealthModelViewSet):
    queryset = CareGapResolution.objects.select_related("care_gap")
    serializer_class = CareGapResolutionSerializer
    filterset_fields = ["care_gap", "resolution_type"]
