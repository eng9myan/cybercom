from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AgencyStaffRegistration, FloatDeployment, FloatPoolMember, StaffingShortageAlert
from .serializers import (
    AgencyStaffRegistrationSerializer,
    FloatDeploymentSerializer,
    FloatPoolMemberSerializer,
    StaffingShortageAlertSerializer,
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


class FloatPoolMemberViewSet(HWMModelViewSet):
    queryset = FloatPoolMember.objects.all()
    serializer_class = FloatPoolMemberSerializer
    filterset_fields = ["facility_id", "is_network_float"]
    ordering_fields = ["priority_score", "created_at"]

    @action(detail=True, methods=["get"])
    def deployments(self, request, pk=None):
        member = self.get_object()
        qs = member.deployments.all()
        serializer = FloatDeploymentSerializer(qs, many=True)
        return Response(serializer.data)


class FloatDeploymentViewSet(HWMModelViewSet):
    queryset = FloatDeployment.objects.select_related("float_member")
    serializer_class = FloatDeploymentSerializer
    filterset_fields = ["float_member", "target_facility_id", "target_department_id", "status"]
    ordering_fields = ["deployed_at", "created_at"]

    @action(detail=True, methods=["post"])
    def recall(self, request, pk=None):
        deployment = self.get_object()
        deployment.status = "recalled"
        deployment.recalled_at = timezone.now()
        deployment.save(update_fields=["status", "recalled_at", "updated_at"])
        return Response({"status": "recalled", "id": str(deployment.id)})


class AgencyStaffRegistrationViewSet(HWMModelViewSet):
    queryset = AgencyStaffRegistration.objects.all()
    serializer_class = AgencyStaffRegistrationSerializer
    filterset_fields = [
        "facility_id",
        "status",
        "credential_verified",
        "identity_verified",
        "ehr_access_token_issued",
    ]
    search_fields = ["display_name", "agency_name", "specialty"]
    ordering_fields = ["contract_start", "contract_end", "created_at"]

    @action(detail=True, methods=["post"])
    def verify_credentials(self, request, pk=None):
        staff = self.get_object()
        staff.credential_verified = True
        staff.credential_verified_at = timezone.now()
        if staff.identity_verified:
            staff.ehr_access_token_issued = True
            staff.status = "active"
        staff.save(
            update_fields=[
                "credential_verified",
                "credential_verified_at",
                "ehr_access_token_issued",
                "status",
                "updated_at",
            ]
        )
        return Response({"status": staff.status, "id": str(staff.id)})

    @action(detail=True, methods=["post"])
    def verify_identity(self, request, pk=None):
        staff = self.get_object()
        staff.identity_verified = True
        staff.identity_verified_at = timezone.now()
        if staff.credential_verified:
            staff.ehr_access_token_issued = True
            staff.status = "active"
        staff.save(
            update_fields=[
                "identity_verified",
                "identity_verified_at",
                "ehr_access_token_issued",
                "status",
                "updated_at",
            ]
        )
        return Response({"status": staff.status, "id": str(staff.id)})


class StaffingShortageAlertViewSet(HWMModelViewSet):
    queryset = StaffingShortageAlert.objects.all()
    serializer_class = StaffingShortageAlertSerializer
    filterset_fields = ["facility_id", "department_id", "escalation_level", "diversion_activated"]
    ordering_fields = ["triggered_at", "created_at"]

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.resolved_at = timezone.now()
        alert.resolution_method = request.data.get("resolution_method", "")
        alert.save(update_fields=["resolved_at", "resolution_method", "updated_at"])
        return Response({"status": "resolved", "id": str(alert.id)})
