from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import WorkforceProfile, ClinicalCredential, CompetencyRecord
from .serializers import (
    WorkforceProfileSerializer,
    ClinicalCredentialSerializer,
    CompetencyRecordSerializer,
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


class WorkforceProfileViewSet(HWMModelViewSet):
    queryset = WorkforceProfile.objects.all()
    serializer_class = WorkforceProfileSerializer
    filterset_fields = ["facility_id", "department_id", "role_type", "clinical_category", "contract_type", "is_active", "is_float_eligible"]
    search_fields = ["display_name", "specialty", "sub_specialty"]
    ordering_fields = ["display_name", "role_type", "created_at"]

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        profile = self.get_object()
        profile.is_active = False
        profile.save(update_fields=["is_active", "updated_at"])
        return Response({"status": "deactivated", "id": str(profile.id)})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        profile = self.get_object()
        profile.is_active = True
        profile.save(update_fields=["is_active", "updated_at"])
        return Response({"status": "activated", "id": str(profile.id)})

    @action(detail=True, methods=["get"])
    def credentials(self, request, pk=None):
        profile = self.get_object()
        qs = profile.credentials.all()
        serializer = ClinicalCredentialSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def competencies(self, request, pk=None):
        profile = self.get_object()
        qs = profile.competencies.filter(is_current=True)
        serializer = CompetencyRecordSerializer(qs, many=True)
        return Response(serializer.data)


class ClinicalCredentialViewSet(HWMModelViewSet):
    queryset = ClinicalCredential.objects.select_related("profile")
    serializer_class = ClinicalCredentialSerializer
    filterset_fields = ["profile", "credential_type", "status"]
    search_fields = ["credential_number", "issuing_body"]
    ordering_fields = ["expiry_date", "created_at"]


class CompetencyRecordViewSet(HWMModelViewSet):
    queryset = CompetencyRecord.objects.select_related("profile")
    serializer_class = CompetencyRecordSerializer
    filterset_fields = ["profile", "competency_code", "is_current"]
    search_fields = ["competency_code", "competency_name"]
    ordering_fields = ["certified_at", "expiry_date", "created_at"]
