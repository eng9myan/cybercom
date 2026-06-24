from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    PopulationGroup,
    PopulationSegment,
    HealthRisk,
    HealthGoal,
    PopulationProgram,
    NationalProvider,
    ProviderCredential,
    NationalFacility,
    FacilityAccreditation,
)
from .serializers import (
    PopulationGroupSerializer,
    PopulationSegmentSerializer,
    HealthRiskSerializer,
    HealthGoalSerializer,
    PopulationProgramSerializer,
    NationalProviderSerializer,
    ProviderCredentialSerializer,
    NationalFacilitySerializer,
    FacilityAccreditationSerializer,
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


class PopulationGroupViewSet(PopulationHealthModelViewSet):
    queryset = PopulationGroup.objects.all()
    serializer_class = PopulationGroupSerializer
    filterset_fields = ["group_type", "is_active"]
    search_fields = ["name", "geographic_scope"]
    ordering_fields = ["name", "estimated_size", "created_at"]


class PopulationSegmentViewSet(PopulationHealthModelViewSet):
    queryset = PopulationSegment.objects.select_related("population_group")
    serializer_class = PopulationSegmentSerializer
    filterset_fields = ["population_group", "is_active"]
    search_fields = ["segment_name"]
    ordering_fields = ["segment_name", "patient_count", "last_calculated_at"]


class HealthRiskViewSet(PopulationHealthModelViewSet):
    queryset = HealthRisk.objects.all()
    serializer_class = HealthRiskSerializer
    filterset_fields = ["patient_id", "risk_type", "risk_level"]
    search_fields = ["risk_type"]
    ordering_fields = ["assessment_date", "risk_score", "created_at"]


class HealthGoalViewSet(PopulationHealthModelViewSet):
    queryset = HealthGoal.objects.all()
    serializer_class = HealthGoalSerializer
    filterset_fields = ["patient_id", "goal_type", "status"]
    search_fields = ["goal_type", "target_value"]
    ordering_fields = ["start_date", "target_date", "created_at"]


class PopulationProgramViewSet(PopulationHealthModelViewSet):
    queryset = PopulationProgram.objects.all()
    serializer_class = PopulationProgramSerializer
    filterset_fields = ["program_type", "status"]
    search_fields = ["name", "target_population_description"]
    ordering_fields = ["name", "start_date", "created_at"]


class NationalProviderViewSet(PopulationHealthModelViewSet):
    queryset = NationalProvider.objects.all()
    serializer_class = NationalProviderSerializer
    filterset_fields = ["provider_type", "registration_status"]
    search_fields = ["national_provider_number", "specialty"]
    ordering_fields = ["registration_date", "created_at"]

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        provider = self.get_object()
        provider.registration_status = "active"
        provider.save(update_fields=["registration_status", "updated_at"])
        return Response({"status": "verified", "id": str(provider.id)})


class ProviderCredentialViewSet(PopulationHealthModelViewSet):
    queryset = ProviderCredential.objects.select_related("national_provider")
    serializer_class = ProviderCredentialSerializer
    filterset_fields = ["national_provider", "credential_type", "is_verified"]
    search_fields = ["credential_number", "issuing_authority"]
    ordering_fields = ["issue_date", "expiry_date", "created_at"]


class NationalFacilityViewSet(PopulationHealthModelViewSet):
    queryset = NationalFacility.objects.all()
    serializer_class = NationalFacilitySerializer
    filterset_fields = ["facility_type", "license_status"]
    search_fields = ["facility_name", "national_facility_number"]
    ordering_fields = ["facility_name", "registration_date", "created_at"]


class FacilityAccreditationViewSet(PopulationHealthModelViewSet):
    queryset = FacilityAccreditation.objects.select_related("national_facility")
    serializer_class = FacilityAccreditationSerializer
    filterset_fields = ["national_facility", "is_current"]
    search_fields = ["accreditation_body", "accreditation_type"]
    ordering_fields = ["award_date", "expiry_date", "created_at"]