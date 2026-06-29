from django.db import models

from platform.common.models import BaseModel


class ImagingOperationsDashboard(BaseModel):
    class Meta:
        app_label = "img_analytics"
        db_table = "cymed_img_ops_dashboard"
        unique_together = [("tenant_id", "snapshot_date", "department")]

    snapshot_date = models.DateField(db_index=True)
    department = models.CharField(max_length=100, blank=True)
    total_orders = models.PositiveIntegerField(default=0)
    studies_completed = models.PositiveIntegerField(default=0)
    reports_finalized = models.PositiveIntegerField(default=0)
    critical_findings = models.PositiveIntegerField(default=0)
    average_tat_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    stat_tat_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    urgent_tat_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    capacity_utilization_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    no_shows = models.PositiveIntegerField(default=0)
    cancellations = models.PositiveIntegerField(default=0)
    by_modality = models.JSONField(default=dict)
    by_priority = models.JSONField(default=dict)

    def __str__(self):
        return f"OpsDB {self.snapshot_date} {self.department}"


class RadiologistProductivity(BaseModel):
    class Meta:
        app_label = "img_analytics"
        db_table = "cymed_img_radiologist_productivity"

    radiologist_id = models.UUIDField(db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        default="daily",
    )
    total_rvu = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    studies_read = models.PositiveIntegerField(default=0)
    reports_finalized = models.PositiveIntegerField(default=0)
    avg_report_tat_hours = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    critical_findings_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    peer_review_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    amendments_issued = models.PositiveIntegerField(default=0)
    by_modality = models.JSONField(default=dict)

    def __str__(self):
        return f"Productivity {self.radiologist_id} — {self.period_start}"


class TeleradiologyDashboard(BaseModel):
    class Meta:
        app_label = "img_analytics"
        db_table = "cymed_img_teleradiology_dashboard"
        unique_together = [("tenant_id", "snapshot_date")]

    snapshot_date = models.DateField(db_index=True)
    total_cases = models.PositiveIntegerField(default=0)
    cases_completed = models.PositiveIntegerField(default=0)
    cases_pending = models.PositiveIntegerField(default=0)
    avg_tat_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    second_opinion_requests = models.PositiveIntegerField(default=0)
    discrepancy_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    by_subspecialty = models.JSONField(default=dict)
    by_facility = models.JSONField(default=dict)
    by_priority = models.JSONField(default=dict)

    def __str__(self):
        return f"TeleDB {self.snapshot_date}"


class ImagingRevenueEvent(BaseModel):
    class Meta:
        app_label = "img_analytics"
        db_table = "cymed_img_revenue_events"

    order_item_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField()
    procedure_code = models.CharField(max_length=100)
    modality = models.CharField(max_length=20)
    rvu_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    event_type = models.CharField(
        max_length=30,
        choices=[
            ("charge_created", "Charge Created"),
            ("charge_voided", "Charge Voided"),
        ],
        default="charge_created",
    )
    outbox_event_id = models.UUIDField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Revenue {self.procedure_code} — {self.event_type}"
