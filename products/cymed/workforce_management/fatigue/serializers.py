from rest_framework import serializers
from .models import DutyHourLog, WeeklyHoursSummary, FatigueViolation, DisasterOverride


class DutyHourLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyHourLog
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class WeeklyHoursSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyHoursSummary
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class FatigueViolationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FatigueViolation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "detected_at", "created_at", "updated_at"]


class DisasterOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisasterOverride
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "activated_at", "created_at", "updated_at"]
