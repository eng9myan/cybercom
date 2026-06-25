from rest_framework import serializers
from .models import PatientAcuityScore, WardCoverageRequirement, CoverageValidationRun, SkillMixValidation


class PatientAcuityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientAcuityScore
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class WardCoverageRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = WardCoverageRequirement
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CoverageValidationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverageValidationRun
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "validated_at", "created_at", "updated_at"]


class SkillMixValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillMixValidation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
