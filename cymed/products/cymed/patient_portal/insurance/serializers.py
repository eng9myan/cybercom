from rest_framework import serializers

from .models import ClaimStatus, CoverageVerification, InsuranceCard, PreauthorizationRequest


class InsuranceCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCard
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CoverageVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverageVerification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PreauthorizationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreauthorizationRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "submitted_at"]


class ClaimStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimStatus
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
