from rest_framework import serializers

from products.cycom.appointments.models import AppointmentType, AvailabilitySlot, Booking, Resource


class AppointmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentType
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ResourceSerializer(serializers.ModelSerializer):
    availability_slots = AvailabilitySlotSerializer(many=True, read_only=True)

    class Meta:
        model = Resource
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class BookingSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source="resource.name", read_only=True)
    appointment_type_name = serializers.CharField(source="appointment_type.name", read_only=True)

    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "end_at", "status", "created_at", "updated_at"]
