from rest_framework import serializers

from .models import (
    ClaimMetricsSnapshot,
    DenialAnalyticsSnapshot,
    PayerPerformanceSnapshot,
    RCMAIInsight,
    RevenueDashboardSnapshot,
    RevenueLeakageAlert,
)


class RevenueDashboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueDashboardSnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ClaimMetricsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimMetricsSnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class DenialAnalyticsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenialAnalyticsSnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class PayerPerformanceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayerPerformanceSnapshot
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class RCMAIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = RCMAIInsight
        fields = "__all__"
        read_only_fields = ["id", "is_advisory_only", "created_at", "updated_at"]


class RevenueLeakageAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueLeakageAlert
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
