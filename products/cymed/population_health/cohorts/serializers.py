from rest_framework import serializers

from .models import Cohort, CohortAnalysis, CohortMember, CohortOutcome


class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CohortMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortMember
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "joined_at"]


class CohortOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortOutcome
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CohortAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortAnalysis
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "is_advisory_only"]
