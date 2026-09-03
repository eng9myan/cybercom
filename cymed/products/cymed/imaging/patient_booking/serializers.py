"""Serializers for CyMed Imaging patient booking."""

from __future__ import annotations

from rest_framework import serializers

from .models import BookableStudy, ImagingBooking, ImagingSlot, ModalityRoom


class BookableStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookableStudy
        fields = "__all__"


class ModalityRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModalityRoom
        fields = "__all__"


class ImagingSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingSlot
        fields = "__all__"


class ImagingBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingBooking
        fields = "__all__"
