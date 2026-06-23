from rest_framework import serializers
from .models import ImagingRoom, ImagingAppointment, ModalitySchedule, RadiologistSchedule


class ImagingRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingRoom
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ImagingAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingAppointment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ModalityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModalitySchedule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RadiologistScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologistSchedule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
