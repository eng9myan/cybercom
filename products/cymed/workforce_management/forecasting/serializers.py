from rest_framework import serializers
from .models import CensusDataPoint, StaffingForecast, ForecastAdjustment, ForecastRosterMapping


class CensusDataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = CensusDataPoint
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StaffingForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffingForecast
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ForecastAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastAdjustment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ForecastRosterMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastRosterMapping
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "applied_at", "created_at", "updated_at"]
