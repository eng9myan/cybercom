from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.appointments.models import AppointmentType, AvailabilitySlot, Booking, Resource
from products.cycom.appointments.serializers import (
    AppointmentTypeSerializer,
    AvailabilitySlotSerializer,
    BookingSerializer,
    ResourceSerializer,
)
from products.cycom.appointments.services import book_appointment, cancel_booking, complete_booking


class AppointmentTypeViewSet(TenantScopedModelViewSet):
    queryset = AppointmentType.objects.all()
    serializer_class = AppointmentTypeSerializer
    filterset_fields = ["is_active"]


class ResourceViewSet(TenantScopedModelViewSet):
    queryset = Resource.objects.prefetch_related("availability_slots").all()
    serializer_class = ResourceSerializer
    filterset_fields = ["is_active"]


class AvailabilitySlotViewSet(TenantScopedModelViewSet):
    queryset = AvailabilitySlot.objects.select_related("resource").all()
    serializer_class = AvailabilitySlotSerializer
    filterset_fields = ["resource", "weekday"]


class BookingViewSet(TenantScopedModelViewSet):
    """create() always goes through book_appointment() — a Booking's end_at
    and validity are never something a raw POST body can set directly."""

    queryset = Booking.objects.select_related("resource", "appointment_type").all()
    serializer_class = BookingSerializer
    filterset_fields = ["resource", "appointment_type", "status"]

    def create(self, request, *args, **kwargs):
        data = request.data
        resource_id = data.get("resource")
        appointment_type_id = data.get("appointment_type")
        start_at_raw = data.get("start_at")
        customer_name = data.get("customer_name")
        if not (resource_id and appointment_type_id and start_at_raw and customer_name):
            raise ValidationError("resource, appointment_type, start_at, and customer_name are required.")

        try:
            resource = Resource.objects.get(pk=resource_id, tenant_id=request.tenant_id)
        except Resource.DoesNotExist:
            raise ValidationError("resource not found.")
        try:
            appointment_type = AppointmentType.objects.get(pk=appointment_type_id, tenant_id=request.tenant_id)
        except AppointmentType.DoesNotExist:
            raise ValidationError("appointment_type not found.")

        # DRF's own DateTimeField parsing, not datetime.fromisoformat —
        # respects USE_TZ the same way every other DRF-parsed datetime in
        # this codebase does, instead of silently accepting a naive
        # datetime that would later crash comparing against aware ones
        # read back from the DB.
        start_at = serializers.DateTimeField().to_internal_value(start_at_raw)
        booking = book_appointment(
            resource=resource,
            appointment_type=appointment_type,
            start_at=start_at,
            customer_name=customer_name,
            customer_email=data.get("customer_email", ""),
        )
        return Response(BookingSerializer(booking).data, status=201)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = cancel_booking(self.get_object())
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        booking = complete_booking(self.get_object())
        return Response(BookingSerializer(booking).data)
