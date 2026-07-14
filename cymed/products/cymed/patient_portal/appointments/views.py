from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    AppointmentRating,
    AppointmentReminder,
    PortalAppointmentRequest,
    WaitlistEntry,
)
from .serializers import (
    AppointmentRatingSerializer,
    AppointmentReminderSerializer,
    PortalAppointmentRequestSerializer,
    PortalAppointmentRequestWriteSerializer,
    WaitlistEntrySerializer,
)


class PortalAppointmentRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "provider_type", "appointment_type", "account_id", "patient_id"]
    search_fields = ["provider_name", "physician_name", "specialty", "chief_complaint"]
    ordering_fields = ["created_at", "preferred_date_1", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return PortalAppointmentRequest.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PortalAppointmentRequestWriteSerializer
        return PortalAppointmentRequestSerializer

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        reason = request.data.get("reason", "")
        cancelled_by = request.data.get("cancelled_by", "patient")
        if appointment.status in ["completed", "cancelled"]:
            return Response(
                {"detail": "Cannot cancel an appointment that is already completed or cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = "cancelled"
        appointment.cancellation_reason = reason
        appointment.cancelled_by = cancelled_by
        appointment.save(
            update_fields=["status", "cancellation_reason", "cancelled_by", "updated_at"]
        )
        serializer = PortalAppointmentRequestSerializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="reminders")
    def reminders(self, request, pk=None):
        appointment = self.get_object()
        reminders = appointment.reminders.all()
        serializer = AppointmentReminderSerializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="rating")
    def rating(self, request, pk=None):
        appointment = self.get_object()
        if request.method == "GET":
            try:
                serializer = AppointmentRatingSerializer(appointment.rating)
                return Response(serializer.data)
            except AppointmentRating.DoesNotExist:
                return Response(
                    {"detail": "No rating found for this appointment."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        serializer = AppointmentRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            appointment_request=appointment,
            account_id=appointment.account_id,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WaitlistEntryViewSet(viewsets.ModelViewSet):
    serializer_class = WaitlistEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "status",
        "priority",
        "waitlist_type",
        "account_id",
        "patient_id",
        "provider_id",
    ]
    search_fields = ["specialty"]
    ordering_fields = ["created_at", "priority", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return WaitlistEntry.objects.filter(tenant_id=self.request.tenant_id)

    @action(detail=True, methods=["post"], url_path="accept-offer")
    def accept_offer(self, request, pk=None):
        entry = self.get_object()
        if entry.status != "offered":
            return Response(
                {"detail": "Only offered waitlist entries can be accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        entry.status = "accepted"
        entry.save(update_fields=["status", "updated_at"])
        serializer = WaitlistEntrySerializer(entry)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        entry = self.get_object()
        if entry.status in ["accepted", "cancelled", "expired"]:
            return Response(
                {"detail": "This waitlist entry cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        entry.status = "cancelled"
        entry.save(update_fields=["status", "updated_at"])
        serializer = WaitlistEntrySerializer(entry)
        return Response(serializer.data)


class AppointmentReminderViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "reminder_type", "appointment_request"]
    ordering_fields = ["scheduled_at", "created_at"]
    ordering = ["scheduled_at"]

    def get_queryset(self):
        return AppointmentReminder.objects.filter(tenant_id=self.request.tenant_id).select_related(
            "appointment_request"
        )


class AppointmentRatingViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["account_id", "would_recommend"]
    ordering_fields = ["created_at", "overall_rating"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return AppointmentRating.objects.filter(tenant_id=self.request.tenant_id).select_related(
            "appointment_request"
        )
