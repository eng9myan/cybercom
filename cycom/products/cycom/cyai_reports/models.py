from django.db import models

from platform.common.models import BaseModel


class ReportBuilderSession(BaseModel):
    """
    A single report-design conversation. Holds the full message history and
    the current draft spec — nothing here is a saved report until the user
    explicitly confirms via ReportBuilderSession -> ReportDefinition.
    """

    STATUS_CHOICES = [
        ("gathering", "Gathering Requirements"),
        ("drafting", "Draft Ready"),
        ("confirmed", "Confirmed & Saved"),
        ("abandoned", "Abandoned"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="gathering")
    messages = models.JSONField(default=list)  # [{role, content, created_at}]
    draft_spec = models.JSONField(null=True, blank=True)
    draft_title = models.CharField(max_length=255, blank=True)
    started_by = models.CharField(max_length=255, blank=True)
    saved_report = models.ForeignKey(
        "ReportDefinition", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_cyai_report_sessions"
        ordering = ["-created_at"]


class ReportDefinition(BaseModel):
    """A saved, confirmed report. Execution (run/export/schedule) never
    needs the LLM again — it just replays query_spec through query_engine."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    query_spec = models.JSONField()
    owner = models.CharField(max_length=255, blank=True)
    is_shared = models.BooleanField(default=False)
    is_pinned_to_dashboard = models.BooleanField(default=False)
    current_version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cycom_cyai_report_definitions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} (v{self.current_version})"


class ReportRevision(BaseModel):
    """Version history — every confirmed change to a report's query_spec."""

    report = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name="revisions")
    version = models.PositiveIntegerField()
    query_spec = models.JSONField()
    change_summary = models.CharField(max_length=255, blank=True)
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_cyai_report_revisions"
        unique_together = [("report", "version")]
        ordering = ["-version"]


class ReportShare(BaseModel):
    report = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name="shares")
    shared_with_email = models.EmailField()
    can_edit = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_cyai_report_shares"
        unique_together = [("report", "shared_with_email")]


class ReportSchedule(BaseModel):
    FORMAT_CHOICES = [("csv", "CSV"), ("json", "JSON")]

    report = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name="schedules")
    cron_expression = models.CharField(max_length=100)  # e.g. "0 8 * * MON"
    recipients = models.JSONField(default=list)  # list of emails
    export_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default="csv")
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_cyai_report_schedules"
