from rest_framework import serializers

from .models import (
    AppointmentRating,
    AppointmentReminder,
    PortalAppointmentRequest,
    WaitlistEntry,
)


class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AppointmentRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentRating
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PortalAppointmentRequestSerializer(serializers.ModelSerializer):
    reminders = AppointmentReminderSerializer(many=True, read_only=True)
    rating = AppointmentRatingSerializer(read_only=True)

    class Meta:
        model = PortalAppointmentRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PortalAppointmentRequestWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalAppointmentRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class WaitlistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitlistEntry
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
