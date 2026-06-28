from rest_framework import serializers
from .models import BIReport, DashboardMetric


class BIReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BIReport
        fields = ["id", "name", "report_type", "query_definition", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DashboardMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardMetric
        fields = ["id", "name", "metric_value", "period", "dimensions", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
