"""
CyMed Population Health — Cohorts ViewSets
"""

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cohort, CohortAnalysis, CohortMember, CohortOutcome
from .serializers import (
    CohortAnalysisSerializer,
    CohortMemberSerializer,
    CohortOutcomeSerializer,
    CohortSerializer,
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


class CohortViewSet(PopulationHealthModelViewSet):
    queryset = Cohort.objects.all()
    serializer_class = CohortSerializer
    filterset_fields = ["cohort_type", "is_active", "is_dynamic"]

    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        cohort = self.get_object()
        active_count = CohortMember.objects.filter(
            cohort=cohort, is_active=True, tenant_id=cohort.tenant_id
        ).count()
        cohort.patient_count = active_count
        cohort.last_updated_at = timezone.now()
        cohort.save(update_fields=["patient_count", "last_updated_at", "updated_at"])
        return Response(CohortSerializer(cohort).data)


class CohortMemberViewSet(PopulationHealthModelViewSet):
    queryset = CohortMember.objects.select_related("cohort")
    serializer_class = CohortMemberSerializer
    filterset_fields = ["cohort", "is_active"]
    search_fields = ["patient_id"]


class CohortOutcomeViewSet(PopulationHealthModelViewSet):
    queryset = CohortOutcome.objects.select_related("cohort")
    serializer_class = CohortOutcomeSerializer
    filterset_fields = ["cohort", "outcome_type", "patient_id"]


class CohortAnalysisViewSet(PopulationHealthModelViewSet):
    queryset = CohortAnalysis.objects.select_related("cohort")
    serializer_class = CohortAnalysisSerializer
    filterset_fields = ["cohort", "analysis_type", "is_ai_generated"]
