from rest_framework import serializers
from .models import (
    ProviderProductivitySnapshot,
    ClinicalQualityMetric,
    WorkforceDashboardSnapshot,
    ProviderAIInsight,
    ExecutiveDashboardMetric,
)


class ProviderProductivitySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderProductivitySnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ClinicalQualityMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalQualityMetric
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkforceDashboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkforceDashboardSnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ProviderAIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAIInsight
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "is_advisory_only"]


class ExecutiveDashboardMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveDashboardMetric
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
