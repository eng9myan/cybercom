from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    DiseaseRegistry,
    RegistryEnrollment,
    RegistryOutcome,
    RegistryPatient,
    RegistryStatus,
)
from .serializers import (
    DiseaseRegistrySerializer,
    RegistryEnrollmentSerializer,
    RegistryOutcomeSerializer,
    RegistryPatientSerializer,
    RegistryStatusSerializer,
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


class DiseaseRegistryViewSet(PopulationHealthModelViewSet):
    queryset = DiseaseRegistry.objects.all()
    serializer_class = DiseaseRegistrySerializer
    filterset_fields = ["registry_type", "is_national", "is_active"]
    search_fields = ["name", "registry_code", "managing_authority"]
    ordering_fields = ["name", "start_date", "created_at"]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        registry = self.get_object()
        registry.is_active = True
        registry.save(update_fields=["is_active", "updated_at"])
        return Response({"status": "activated", "id": str(registry.id)})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        registry = self.get_object()
        registry.is_active = False
        registry.save(update_fields=["is_active", "updated_at"])
        return Response({"status": "deactivated", "id": str(registry.id)})


class RegistryPatientViewSet(PopulationHealthModelViewSet):
    queryset = RegistryPatient.objects.select_related("registry")
    serializer_class = RegistryPatientSerializer
    filterset_fields = ["registry", "status", "enrollment_source"]
    search_fields = ["national_id_hash", "primary_icd11_code"]
    ordering_fields = ["enrollment_date", "created_at"]


class RegistryEnrollmentViewSet(PopulationHealthModelViewSet):
    queryset = RegistryEnrollment.objects.select_related("registry_patient")
    serializer_class = RegistryEnrollmentSerializer
    filterset_fields = ["registry_patient"]
    ordering_fields = ["created_at"]


class RegistryStatusViewSet(PopulationHealthModelViewSet):
    queryset = RegistryStatus.objects.select_related("registry_patient")
    serializer_class = RegistryStatusSerializer
    filterset_fields = ["registry_patient", "status"]
    ordering_fields = ["status_date", "created_at"]
    http_method_names = ["get", "head", "options"]


class RegistryOutcomeViewSet(PopulationHealthModelViewSet):
    queryset = RegistryOutcome.objects.select_related("registry_patient")
    serializer_class = RegistryOutcomeSerializer
    filterset_fields = ["registry_patient", "outcome_type"]
    search_fields = ["icd11_code", "outcome_description"]
    ordering_fields = ["outcome_date", "created_at"]
