from rest_framework import serializers
from .models import CareGap, CareGapRule, CareGapRecommendation, CareGapResolution


class CareGapSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareGap
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CareGapRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareGapRule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CareGapRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareGapRecommendation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "recommendation_date"]


class CareGapResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareGapResolution
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
