"""DRF serializers for the home_collection sub-app."""

from __future__ import annotations

from rest_framework import serializers

from .models import (
    HomeCollectionBooking,
    HomeCollectionEvent,
    HomeCollectionSlot,
    Phlebotomist,
)


class PhlebotomistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phlebotomist
        fields = "__all__"


class HomeCollectionSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeCollectionSlot
        fields = "__all__"


class HomeCollectionBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeCollectionBooking
        fields = "__all__"


class HomeCollectionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeCollectionEvent
        fields = "__all__"
