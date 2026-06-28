from rest_framework import serializers
from .models import (
    CommandCenterSnapshot, CommandCenterAlert, CapacityThreshold,
    HospitalDiversionStatus, BedTurnoverLog, CommandCenterKPI,
)


class CommandCenterSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandCenterSnapshot
        fields = [
            "id", "snapshot_time", "total_beds", "occupied_beds", "available_beds",
            "icu_total", "icu_occupied", "ed_visits_active", "ed_waiting", "ed_lwbs",
            "or_cases_scheduled", "or_cases_in_progress", "pending_admissions",
            "pending_discharges", "pending_transfers", "occupancy_pct",
            "icu_occupancy_pct", "capacity_status", "rn_on_duty", "md_on_duty",
            "hap_infections_mtd", "falls_mtd", "pressure_injuries_mtd",
            "patient_satisfaction_score",
        ]
        read_only_fields = ["id", "snapshot_time"]


class CommandCenterAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandCenterAlert
        fields = [
            "id", "alert_code", "title", "title_ar", "description", "severity",
            "status", "category", "department", "location", "triggered_at",
            "acknowledged_at", "acknowledged_by", "resolved_at", "resolved_by",
            "resolution_notes", "escalated_at", "escalated_to", "metadata",
        ]
        read_only_fields = ["id", "triggered_at"]


class AlertAcknowledgeSerializer(serializers.Serializer):
    acknowledged_by = serializers.CharField(max_length=255)


class AlertResolveSerializer(serializers.Serializer):
    resolved_by = serializers.CharField(max_length=255)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class AlertEscalateSerializer(serializers.Serializer):
    escalated_to = serializers.CharField(max_length=255)


class CapacityThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapacityThreshold
        fields = [
            "id", "unit_name", "unit_code", "total_capacity",
            "elevated_threshold_pct", "high_threshold_pct", "critical_threshold_pct",
            "auto_alert_enabled", "is_active",
        ]
        read_only_fields = ["id"]


class HospitalDiversionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalDiversionStatus
        fields = [
            "id", "diversion_type", "started_at", "ended_at", "reason",
            "approved_by", "notified_agencies", "is_active",
        ]
        read_only_fields = ["id"]


class BedTurnoverLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedTurnoverLog
        fields = [
            "id", "bed_id", "unit_name", "patient_discharge_time",
            "cleaning_start_time", "cleaning_end_time",
            "next_patient_admitted_time", "turnaround_minutes",
        ]
        read_only_fields = ["id"]


class CommandCenterKPISerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandCenterKPI
        fields = [
            "id", "kpi_date", "kpi_name", "kpi_value", "kpi_unit",
            "target_value", "department", "metadata",
        ]
        read_only_fields = ["id"]
