"""Models for the CyMed ecosystem analytics sub-app."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class AnalyticsSnapshot(BaseModel):
    class Kind(models.TextChoices):
        PATIENT_FLOW = "patient_flow", "Patient Flow"
        REVENUE = "revenue", "Revenue"
        REFERRAL_NETWORK = "referral_network", "Referral Network"
        PROVIDER_UTILISATION = "provider_utilisation", "Provider Utilisation"
        WAIT_TIMES = "wait_times", "Wait Times"
        ADHERENCE = "adherence", "Adherence"
        RETENTION = "retention", "Retention"
        CLAIM_KPIS = "claim_kpis", "Claim KPIs"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    snapshot_date = models.DateField()
    kind = models.CharField(max_length=32, choices=Kind.choices)
    payload = models.JSONField(default=dict)
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_eco_analytics_snapshot"
        unique_together = [("tenant_id", "snapshot_date", "kind")]

    def __str__(self) -> str:
        return f"AnalyticsSnapshot({self.kind}, {self.snapshot_date})"


class Dashboard(BaseModel):
    class Audience(models.TextChoices):
        EXECUTIVE = "executive", "Executive"
        CLINICAL = "clinical", "Clinical"
        OPERATIONS = "operations", "Operations"
        COMMERCIAL = "commercial", "Commercial"
        REGULATOR = "regulator", "Regulator"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True)
    audience = models.CharField(max_length=32, choices=Audience.choices)
    layout = models.JSONField(default=dict)
    shared_with_tenant_ids = models.JSONField(default=list)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_eco_analytics_dashboard"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"Dashboard({self.code})"


class DashboardWidget(BaseModel):
    class Kind(models.TextChoices):
        KPI = "kpi", "KPI"
        LINE = "line", "Line"
        BAR = "bar", "Bar"
        PIE = "pie", "Pie"
        HEATMAP = "heatmap", "Heatmap"
        GEOMAP = "geomap", "Geomap"
        FUNNEL = "funnel", "Funnel"
        COHORT = "cohort", "Cohort"
        TABLE = "table", "Table"

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name="widgets",
    )
    position = models.IntegerField(default=0)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=255)
    data_source = models.CharField(max_length=64)
    params = models.JSONField(default=dict)

    class Meta:
        db_table = "cymed_eco_analytics_dashboard_widget"

    def __str__(self) -> str:
        return f"DashboardWidget({self.kind}, {self.title})"


class AnalyticsExport(BaseModel):
    class Kind(models.TextChoices):
        CSV = "csv", "CSV"
        XLSX = "xlsx", "XLSX"
        PDF = "pdf", "PDF"
        JSON = "json", "JSON"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    requested_by_profile_id = models.UUIDField(null=True, blank=True)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    filter_payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    file_url = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_eco_analytics_export"

    def __str__(self) -> str:
        return f"AnalyticsExport({self.kind}, {self.status})"
