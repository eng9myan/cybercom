from rest_framework import serializers

from .models import RiskAssessment, RiskCategory, RiskFactor, RiskScore


class RiskScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskScore
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "is_advisory_only"]


class RiskFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskFactor
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RiskCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskCategory
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "is_advisory_only"]
