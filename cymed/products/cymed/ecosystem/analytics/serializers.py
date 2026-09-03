"""DRF serializers for the CyMed ecosystem analytics sub-app."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    AnalyticsExport,
    AnalyticsSnapshot,
    Dashboard,
    DashboardWidget,
)


class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsSnapshot
        fields = "__all__"


class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = "__all__"


class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = "__all__"


class AnalyticsExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsExport
        fields = "__all__"
