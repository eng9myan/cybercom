"""DRF serializers for provider directory models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    DirectoryReview,
    NetworkFacility,
    NetworkPractitioner,
    PractitionerFacilityAffiliation,
)


class NetworkFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkFacility
        fields = "__all__"


class NetworkPractitionerSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkPractitioner
        fields = "__all__"


class PractitionerFacilityAffiliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PractitionerFacilityAffiliation
        fields = "__all__"


class DirectoryReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectoryReview
        fields = "__all__"
