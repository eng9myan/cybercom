from rest_framework import serializers
from .models import PharmacyDashboardSnapshot, MedicationSafetyEvent, PharmacyAnalyticsConfig


class PharmacyDashboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyDashboardSnapshot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MedicationSafetyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationSafetyEvent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "discovered_at"]


class PharmacyAnalyticsConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyAnalyticsConfig
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
