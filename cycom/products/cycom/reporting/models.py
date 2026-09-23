from django.db import models

from platform.common.models import BaseModel
from products.cycom.reporting.registry import source_choices

AGGREGATION_CHOICES = [
    ("sum", "Sum"),
    ("avg", "Average"),
    ("count", "Count"),
]

CHART_TYPE_CHOICES = [
    ("table", "Table"),
    ("bar", "Bar Chart"),
    ("pie", "Pie Chart"),
]


class SavedReport(BaseModel):
    """A pivot: group `source` rows by `dimension`, aggregate `measure`.
    `dimension`/`measure` are plain strings (not FK/choices) because their
    valid values depend on `source` — validated against
    reporting.registry.REPORT_SOURCES in the serializer, not at the DB
    layer."""

    name = models.CharField(max_length=255)
    source = models.CharField(max_length=40, choices=source_choices())
    dimension = models.CharField(max_length=60)
    measure = models.CharField(max_length=60)
    aggregation = models.CharField(max_length=10, choices=AGGREGATION_CHOICES, default="sum")
    chart_type = models.CharField(max_length=10, choices=CHART_TYPE_CHOICES, default="table")

    class Meta:
        db_table = "cycom_reporting_saved_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
