from rest_framework import serializers

from .models import (
    ImagingOperationsDashboard,
    ImagingRevenueEvent,
    RadiologistProductivity,
    TeleradiologyDashboard,
)


class ImagingOperationsDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingOperationsDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RadiologistProductivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologistProductivity
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TeleradiologyDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeleradiologyDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ImagingRevenueEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingRevenueEvent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
