from django.db import models
from platform.common.models import BaseModel


class BIReport(BaseModel):
    REPORT_TYPE_CHOICES = [
        ("financial", "Financial"),
        ("operations", "Operations"),
        ("clinical", "Clinical"),
        ("hr", "Human Resources"),
    ]

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    query_definition = models.TextField()  # SQL or JSON query representation
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_bi_reports"

    def __str__(self):
        return f"{self.name} ({self.report_type})"


class DashboardMetric(BaseModel):
    name = models.CharField(max_length=255)
    metric_value = models.DecimalField(max_digits=18, decimal_places=4)
    period = models.CharField(max_length=50, default="daily")  # e.g., daily, monthly, real-time
    dimensions = models.JSONField(default=dict, blank=True)   # metadata like department=1, store=North

    class Meta:
        db_table = "cycom_bi_dashboard_metrics"
