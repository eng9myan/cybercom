"""DRF serializers for CyMed Pharmacy Loyalty & Rewards."""
from rest_framework import serializers

from .models import (
    LoyaltyProgram,
    LoyaltyTier,
    PatientLoyaltyAccount,
    PointsTransaction,
    Redemption,
    Reward,
)


class LoyaltyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyProgram
        fields = "__all__"


class LoyaltyTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyTier
        fields = "__all__"


class PatientLoyaltyAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientLoyaltyAccount
        fields = "__all__"


class PointsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsTransaction
        fields = "__all__"


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = "__all__"


class RedemptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redemption
        fields = "__all__"
