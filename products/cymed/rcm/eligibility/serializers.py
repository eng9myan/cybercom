from rest_framework import serializers
from .models import (
    EligibilityRequest,
    EligibilityResponse,
    CoverageVerification,
    BenefitVerification,
)


class EligibilityRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EligibilityRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class EligibilityResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EligibilityResponse
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class BenefitVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenefitVerification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CoverageVerificationSerializer(serializers.ModelSerializer):
    benefit_verifications = BenefitVerificationSerializer(many=True, read_only=True)

    class Meta:
        model = CoverageVerification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CoverageVerificationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverageVerification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
