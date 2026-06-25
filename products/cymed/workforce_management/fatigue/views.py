from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import DutyHourLog, WeeklyHoursSummary, FatigueViolation, DisasterOverride
from .serializers import (
    DutyHourLogSerializer,
    WeeklyHoursSummarySerializer,
    FatigueViolationSerializer,
    DisasterOverrideSerializer,
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


class DutyHourLogViewSet(HWMModelViewSet):
    queryset = DutyHourLog.objects.all()
    serializer_class = DutyHourLogSerializer
    filterset_fields = ["workforce_profile_id", "facility_id", "is_resident", "is_night_shift", "is_weekend"]
    ordering_fields = ["clock_in", "hours_worked", "created_at"]


class WeeklyHoursSummaryViewSet(HWMModelViewSet):
    queryset = WeeklyHoursSummary.objects.all()
    serializer_class = WeeklyHoursSummarySerializer
    filterset_fields = ["workforce_profile_id", "week_start", "is_resident"]
    ordering_fields = ["week_start", "total_hours", "created_at"]
    http_method_names = ["get", "post", "head", "options"]


class FatigueViolationViewSet(HWMModelViewSet):
    queryset = FatigueViolation.objects.all()
    serializer_class = FatigueViolationSerializer
    filterset_fields = ["workforce_profile_id", "violation_type", "status", "prescribing_authority_revoked"]
    ordering_fields = ["detected_at", "status", "created_at"]

    @action(detail=True, methods=["post"])
    def override(self, request, pk=None):
        violation = self.get_object()
        violation.status = "overridden"
        violation.override_by_id = request.data.get("override_by_id")
        violation.override_reason = request.data.get("override_reason", "")
        violation.save(update_fields=["status", "override_by_id", "override_reason", "updated_at"])
        return Response({"status": "overridden", "id": str(violation.id)})

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        violation = self.get_object()
        violation.status = "resolved"
        violation.resolved_at = timezone.now()
        violation.save(update_fields=["status", "resolved_at", "updated_at"])
        return Response({"status": "resolved", "id": str(violation.id)})


class DisasterOverrideViewSet(HWMModelViewSet):
    queryset = DisasterOverride.objects.all()
    serializer_class = DisasterOverrideSerializer
    filterset_fields = ["facility_id", "incident_id", "is_active", "authorized_by_id"]
    ordering_fields = ["activated_at", "created_at"]

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        override = self.get_object()
        override.is_active = False
        override.deactivated_at = timezone.now()
        override.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        return Response({"status": "deactivated", "id": str(override.id)})
