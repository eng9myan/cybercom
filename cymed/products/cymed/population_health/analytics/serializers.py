from rest_framework import serializers

from .models import (
    NationalHealthSnapshot,
    OutbreakForecast,
    PopulationAnalyticsInsight,
    PopulationHealthDashboard,
    QualityKPIDashboard,
)


class NationalHealthSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalHealthSnapshot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PopulationAnalyticsInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationAnalyticsInsight
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "is_advisory_only"]


class QualityKPIDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityKPIDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class OutbreakForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutbreakForecast
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "is_advisory_only"]


class PopulationHealthDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationHealthDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
