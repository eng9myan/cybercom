from rest_framework import serializers
from .models import WorkforceAnalyticsSnapshot, WorkforceReport, OnCallSLAMetric


class WorkforceAnalyticsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkforceAnalyticsSnapshot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class WorkforceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkforceReport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "generated_at", "created_at", "updated_at"]


class OnCallSLAMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnCallSLAMetric
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
