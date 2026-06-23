from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from products.cymed.provider_portal.workforce.models import (
    ProviderSchedule,
    ShiftAssignment,
    LeaveRequest,
    AttendanceRecord,
    CredentialExpiry,
)
from products.cymed.provider_portal.workforce.serializers import (
    ProviderScheduleSerializer,
    ShiftAssignmentSerializer,
    LeaveRequestSerializer,
    AttendanceRecordSerializer,
    CredentialExpirySerializer,
)


class ProviderScheduleViewSet(viewsets.ModelViewSet):
    queryset = ProviderSchedule.objects.all()
    serializer_class = ProviderScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["provider_id", "unit_id", "schedule_date", "shift_type", "status"]
    search_fields = ["provider_name", "unit_name", "department", "location"]
    ordering_fields = ["schedule_date", "shift_start", "created_at"]
    ordering = ["-schedule_date"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class ShiftAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ShiftAssignment.objects.all()
    serializer_class = ShiftAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["schedule", "original_provider_id", "covering_provider_id", "assignment_type", "is_approved"]
    search_fields = []
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["provider_id", "leave_type", "status", "start_date", "end_date"]
    search_fields = ["provider_name", "reason"]
    ordering_fields = ["start_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["provider_id", "attendance_date", "status"]
    search_fields = ["provider_name"]
    ordering_fields = ["attendance_date", "created_at"]
    ordering = ["-attendance_date"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class CredentialExpiryViewSet(viewsets.ModelViewSet):
    queryset = CredentialExpiry.objects.all()
    serializer_class = CredentialExpirySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["provider_id", "credential_type", "alert_status", "is_acknowledged"]
    search_fields = ["provider_name", "credential_name", "credential_number", "issuing_authority"]
    ordering_fields = ["expiry_date", "days_until_expiry", "created_at"]
    ordering = ["expiry_date"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
