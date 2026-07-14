from rest_framework import serializers

from .models import HealthProgram, ProgramEnrollment, ProgramMetric, ProgramOutcome


class HealthProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProgram
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProgramEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramEnrollment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProgramOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramOutcome
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProgramMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramMetric
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
