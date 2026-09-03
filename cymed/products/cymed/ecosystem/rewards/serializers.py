"""DRF serializers for ecosystem-wide loyalty models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    EcosystemAccount,
    EcosystemPointsEvent,
    EcosystemProgram,
    EcosystemRedemption,
    EcosystemReward,
    EcosystemTier,
)


class EcosystemProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcosystemProgram
        fields = "__all__"


class EcosystemAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcosystemAccount
        fields = "__all__"


class EcosystemTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcosystemTier
        fields = "__all__"


class EcosystemPointsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcosystemPointsEvent
        fields = "__all__"


class EcosystemRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcosystemReward
        fields = "__all__"


class EcosystemRedemptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcosystemRedemption
        fields = "__all__"
