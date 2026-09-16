from django.db import models

from platform.common.models import BaseModel


class NCCDRecord(BaseModel):
    """
    Nationally Consistent Collection of Data on School Students with Disability.
    One record per student per collection year: category of disability + level
    of adjustment provided. Drives the annual NCCD return.
    """

    CATEGORY_CHOICES = [
        ("cognitive", "Cognitive"),
        ("physical", "Physical"),
        ("sensory", "Sensory"),
        ("social_emotional", "Social/Emotional"),
    ]
    ADJUSTMENT_CHOICES = [
        ("qdtp", "Support provided within quality differentiated teaching practice"),
        ("supplementary", "Supplementary"),
        ("substantial", "Substantial"),
        ("extensive", "Extensive"),
    ]

    student = models.ForeignKey("cyed_sis.Student", on_delete=models.CASCADE, related_name="nccd_records")
    collection_year = models.PositiveSmallIntegerField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    level_of_adjustment = models.CharField(max_length=20, choices=ADJUSTMENT_CHOICES)
    evidence_note = models.TextField(blank=True)
    imputed_disability = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_nccd_records"
        ordering = ["-collection_year", "student__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "student", "collection_year"],
                name="uniq_nccd_student_year",
            )
        ]

    def __str__(self):
        return f"NCCD {self.student_id} {self.collection_year} {self.level_of_adjustment}"


class StatutoryReportLog(BaseModel):
    """Audit trail of a generated statutory export (who ran what, when)."""

    REPORT_CHOICES = [
        ("nccd", "NCCD Return"),
        ("attendance", "Attendance Return"),
        ("naplan", "NAPLAN Participation"),
        ("census", "National Census (SES/demographics)"),
    ]

    report_type = models.CharField(max_length=20, choices=REPORT_CHOICES)
    period = models.CharField(max_length=40, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    generated_by = models.CharField(max_length=255, blank=True)
    fmt = models.CharField(max_length=10, default="json")

    class Meta:
        db_table = "cyed_statutory_report_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.report_type} {self.period} ({self.row_count})"
