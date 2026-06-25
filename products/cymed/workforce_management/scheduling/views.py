from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ShiftTemplate, RosterCycle, RosterSlot, SelfScheduleWindow, SlotQuota
from .serializers import (
    ShiftTemplateSerializer,
    RosterCycleSerializer,
    RosterSlotSerializer,
    SelfScheduleWindowSerializer,
    SlotQuotaSerializer,
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


class ShiftTemplateViewSet(HWMModelViewSet):
    queryset = ShiftTemplate.objects.all()
    serializer_class = ShiftTemplateSerializer
    filterset_fields = ["shift_type", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["name", "start_time", "created_at"]


class RosterCycleViewSet(HWMModelViewSet):
    queryset = RosterCycle.objects.all()
    serializer_class = RosterCycleSerializer
    filterset_fields = ["facility_id", "department_id", "status"]
    ordering_fields = ["period_start", "status", "created_at"]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        cycle = self.get_object()
        cycle.status = "published"
        cycle.published_by_id = request.user.id if hasattr(request, "user") else None
        cycle.published_at = timezone.now()
        cycle.save(update_fields=["status", "published_by_id", "published_at", "updated_at"])
        return Response({"status": "published", "id": str(cycle.id)})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        cycle = self.get_object()
        cycle.status = "closed"
        cycle.save(update_fields=["status", "updated_at"])
        return Response({"status": "closed", "id": str(cycle.id)})

    @action(detail=True, methods=["get"])
    def slots(self, request, pk=None):
        cycle = self.get_object()
        qs = cycle.slots.select_related("shift_template").all()
        serializer = RosterSlotSerializer(qs, many=True)
        return Response(serializer.data)


class RosterSlotViewSet(HWMModelViewSet):
    queryset = RosterSlot.objects.select_related("roster_cycle", "shift_template")
    serializer_class = RosterSlotSerializer
    filterset_fields = ["roster_cycle", "workforce_profile_id", "shift_template", "status", "slot_date", "is_weekend", "is_holiday"]
    ordering_fields = ["slot_date", "status", "created_at"]

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        slot = self.get_object()
        slot.status = "checked_in"
        slot.checked_in_at = timezone.now()
        slot.save(update_fields=["status", "checked_in_at", "updated_at"])
        return Response({"status": "checked_in", "id": str(slot.id)})

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        slot = self.get_object()
        slot.status = "completed"
        slot.checked_out_at = timezone.now()
        slot.save(update_fields=["status", "checked_out_at", "updated_at"])
        return Response({"status": "completed", "id": str(slot.id)})


class SelfScheduleWindowViewSet(HWMModelViewSet):
    queryset = SelfScheduleWindow.objects.select_related("roster_cycle")
    serializer_class = SelfScheduleWindowSerializer
    filterset_fields = ["roster_cycle", "is_active"]
    ordering_fields = ["opens_at", "closes_at", "created_at"]


class SlotQuotaViewSet(HWMModelViewSet):
    queryset = SlotQuota.objects.select_related("roster_cycle", "shift_template")
    serializer_class = SlotQuotaSerializer
    filterset_fields = ["roster_cycle", "shift_template", "slot_date", "is_locked"]
    ordering_fields = ["slot_date", "created_at"]
