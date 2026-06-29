from rest_framework import serializers

from .models import DiseaseTrend, EpidemiologyStudy, HealthMeasure, PopulationIndicator


class EpidemiologyStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = EpidemiologyStudy
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DiseaseTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseTrend
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PopulationIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationIndicator
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class HealthMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthMeasure
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
