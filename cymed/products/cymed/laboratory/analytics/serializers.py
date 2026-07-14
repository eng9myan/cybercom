from rest_framework import serializers

from .models import (
    LabMicrobiologyDashboard,
    LabOperationsDashboard,
    LabProductivityReport,
    LabQualityDashboard,
    LabTurnaroundMetric,
)


class LabOperationsDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOperationsDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LabTurnaroundMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTurnaroundMetric
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LabProductivityReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabProductivityReport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LabQualityDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabQualityDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LabMicrobiologyDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabMicrobiologyDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
