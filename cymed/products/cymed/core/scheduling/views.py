from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.canonical import events as canonical_events
from products.cymed.core.scheduling.models import Appointment, ScheduleSlot
from products.cymed.core.scheduling.serializers import AppointmentSerializer, ScheduleSlotSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancels an appointment."""
        appt = self.get_object()
        appt.status = "cancelled"
        appt.save()

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        canonical_events.emit(
            event_type="cymed.appointment.cancelled",
            aggregate_type="Appointment",
            aggregate_id=appt.id,
            tenant_id=appt.tenant_id,
            payload={"appointment_id": str(appt.id), "cancelled_by": str(request.user)},
        )

        return Response({"status": appt.status})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Marks appointment as completed."""
        appt = self.get_object()
        appt.status = "fulfilled"
        appt.save()

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        canonical_events.emit(
            event_type="cymed.appointment.completed",
            aggregate_type="Appointment",
            aggregate_id=appt.id,
            tenant_id=appt.tenant_id,
            payload={"appointment_id": str(appt.id)},
        )

        return Response({"status": appt.status})


class ScheduleSlotViewSet(viewsets.ModelViewSet):
    queryset = ScheduleSlot.objects.all()
    serializer_class = ScheduleSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
