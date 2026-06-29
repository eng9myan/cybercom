from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from products.cymed.provider_portal.patient_lists.models import (
    PatientAssignment,
    PatientCensus,
    PatientList,
    ProviderAssignment,
)
from products.cymed.provider_portal.patient_lists.serializers import (
    PatientAssignmentSerializer,
    PatientCensusSerializer,
    PatientListSerializer,
    ProviderAssignmentSerializer,
)


class PatientListViewSet(viewsets.ModelViewSet):
    queryset = PatientList.objects.all()
    serializer_class = PatientListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["list_type", "is_shared", "is_active", "workspace_id"]
    search_fields = ["name", "specialty"]
    ordering_fields = ["name", "created_at", "patient_count"]
    ordering = ["name"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class PatientAssignmentViewSet(viewsets.ModelViewSet):
    queryset = PatientAssignment.objects.all()
    serializer_class = PatientAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_list", "is_active", "is_primary", "patient_id"]
    search_fields = ["bed_number", "unit_name", "notes"]
    ordering_fields = ["added_at", "admission_date", "acuity_score"]
    ordering = ["-added_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class ProviderAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ProviderAssignment.objects.all()
    serializer_class = ProviderAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["patient_id", "provider_id", "role", "coverage_type", "is_primary"]
    ordering_fields = ["effective_from", "effective_until", "created_at"]
    ordering = ["-effective_from"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class PatientCensusViewSet(viewsets.ModelViewSet):
    queryset = PatientCensus.objects.all()
    serializer_class = PatientCensusSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["unit_id", "census_date"]
    search_fields = ["unit_name"]
    ordering_fields = ["census_date", "occupied_beds", "available_beds"]
    ordering = ["-census_date"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)
