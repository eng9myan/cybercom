"""DRF serializers for CyMed shared capacity models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    RadiologistPoolShift,
    ResourceMatch,
    ResourceOffer,
    ResourceRequest,
)


class ResourceOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceOffer
        fields = "__all__"


class ResourceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceRequest
        fields = "__all__"


class ResourceMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceMatch
        fields = "__all__"


class RadiologistPoolShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologistPoolShift
        fields = "__all__"
