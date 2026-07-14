from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from .models import (
    CoverageValidationRun,
    PatientAcuityScore,
    SkillMixValidation,
    WardCoverageRequirement,
)
from .serializers import (
    CoverageValidationRunSerializer,
    PatientAcuityScoreSerializer,
    SkillMixValidationSerializer,
    WardCoverageRequirementSerializer,
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


class PatientAcuityScoreViewSet(HWMModelViewSet):
    queryset = PatientAcuityScore.objects.all()
    serializer_class = PatientAcuityScoreSerializer
    filterset_fields = ["patient_id", "ward_id", "facility_id", "acuity_level"]
    ordering_fields = ["scored_at", "acuity_level", "created_at"]


class WardCoverageRequirementViewSet(HWMModelViewSet):
    queryset = WardCoverageRequirement.objects.all()
    serializer_class = WardCoverageRequirementSerializer
    filterset_fields = [
        "facility_id",
        "ward_type",
        "physician_coverage_24_7",
        "specialty_cert_required_100pct",
    ]
    ordering_fields = ["ward_type", "created_at"]


class CoverageValidationRunViewSet(HWMModelViewSet):
    queryset = CoverageValidationRun.objects.all()
    serializer_class = CoverageValidationRunSerializer
    filterset_fields = ["roster_cycle_id", "facility_id", "overall_status"]
    ordering_fields = ["validated_at", "created_at"]
    http_method_names = ["get", "post", "head", "options"]


class SkillMixValidationViewSet(HWMModelViewSet):
    queryset = SkillMixValidation.objects.all()
    serializer_class = SkillMixValidationSerializer
    filterset_fields = ["roster_cycle_id", "ward_id", "slot_date", "passed", "charge_nurse_present"]
    ordering_fields = ["slot_date", "created_at"]
    http_method_names = ["get", "post", "head", "options"]
