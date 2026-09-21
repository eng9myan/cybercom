from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.events.models import Event, Registration, TicketType
from products.cycom.events.serializers import (
    EventSerializer,
    RegistrationSerializer,
    TicketTypeSerializer,
)
from products.cycom.events.services import cancel_registration, check_in, register_attendee


class EventViewSet(TenantScopedModelViewSet):
    queryset = Event.objects.prefetch_related("ticket_types").all()
    serializer_class = EventSerializer
    filterset_fields = ["is_published"]

    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        event = self.get_object()
        attendee_name = request.data.get("attendee_name")
        if not attendee_name:
            raise ValidationError("attendee_name is required.")

        ticket_type = None
        ticket_type_id = request.data.get("ticket_type")
        if ticket_type_id:
            try:
                ticket_type = TicketType.objects.get(pk=ticket_type_id, tenant_id=event.tenant_id)
            except TicketType.DoesNotExist:
                raise ValidationError("ticket_type not found.")

        registration = register_attendee(
            event,
            attendee_name=attendee_name,
            attendee_email=request.data.get("attendee_email", ""),
            ticket_type=ticket_type,
        )
        return Response(RegistrationSerializer(registration).data, status=201)


class TicketTypeViewSet(TenantScopedModelViewSet):
    queryset = TicketType.objects.select_related("event").all()
    serializer_class = TicketTypeSerializer
    filterset_fields = ["event"]


class RegistrationViewSet(TenantScopedModelViewSet):
    queryset = Registration.objects.select_related("event", "ticket_type").all()
    serializer_class = RegistrationSerializer
    filterset_fields = ["event", "ticket_type", "status"]

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in_action(self, request, pk=None):
        registration = check_in(self.get_object())
        return Response(RegistrationSerializer(registration).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        registration = cancel_registration(self.get_object())
        return Response(RegistrationSerializer(registration).data)
