"""Serializers for CyMed Laboratory Online Test Booking."""
from rest_framework import serializers

from .models import BookableTest, LabAppointmentSlot, LabBooking, LabPackage


class BookableTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookableTest
        fields = "__all__"


class LabPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabPackage
        fields = "__all__"


class LabAppointmentSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabAppointmentSlot
        fields = "__all__"


class LabBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabBooking
        fields = "__all__"
