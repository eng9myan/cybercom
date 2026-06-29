"""
CyMed Population Health — Risk Management ViewSets
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import RiskAssessment, RiskCategory, RiskFactor, RiskScore
from .serializers import (
    RiskAssessmentSerializer,
    RiskCategorySerializer,
    RiskFactorSerializer,
    RiskScoreSerializer,
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


class RiskScoreViewSet(PopulationHealthModelViewSet):
    queryset = RiskScore.objects.all()
    serializer_class = RiskScoreSerializer
    filterset_fields = [
        "patient_id",
        "risk_category",
        "risk_level",
        "score_date",
        "is_ai_generated",
    ]


class RiskFactorViewSet(PopulationHealthModelViewSet):
    queryset = RiskFactor.objects.select_related("risk_score")
    serializer_class = RiskFactorSerializer
    filterset_fields = ["risk_score", "factor_type"]


class RiskCategoryViewSet(PopulationHealthModelViewSet):
    queryset = RiskCategory.objects.all()
    serializer_class = RiskCategorySerializer
    filterset_fields = ["is_active"]
    search_fields = ["category_code", "category_name"]


class RiskAssessmentViewSet(PopulationHealthModelViewSet):
    queryset = RiskAssessment.objects.all()
    serializer_class = RiskAssessmentSerializer
    filterset_fields = ["patient_id", "overall_risk_level", "status", "is_ai_generated"]

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        assessment = self.get_object()
        user_id = request.data.get("acknowledged_by_user_id") or getattr(request.user, "id", None)
        assessment.status = "acknowledged"
        assessment.acknowledged_by_user_id = user_id
        assessment.save(update_fields=["status", "acknowledged_by_user_id", "updated_at"])
        return Response(RiskAssessmentSerializer(assessment).data)
