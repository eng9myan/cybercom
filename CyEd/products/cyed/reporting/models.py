from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel
from products.cyed.sis.models import AcademicYear, ClassSection, Student


class ReportCard(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="report_cards")
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.SET_NULL, null=True, blank=True, related_name="report_cards"
    )
    term = models.CharField(max_length=50, default="Semester 1")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    published_on = models.DateTimeField(null=True, blank=True)
    general_comment = models.TextField(blank=True)

    class Meta:
        db_table = "cyed_report_cards"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year", "term"], name="uniq_reportcard_student_year_term"
            )
        ]

    def publish(self):
        self.status = "published"
        self.published_on = timezone.now()
        self.save(update_fields=["status", "published_on", "updated_at"])

    def __str__(self):
        return f"{self.student_id} {self.term} ({self.status})"


class ReportCardEntry(BaseModel):
    ACHIEVEMENT_CHOICES = [
        ("A", "A — Excellent"),
        ("B", "B — Good"),
        ("C", "C — Satisfactory"),
        ("D", "D — Limited"),
        ("E", "E — Very Low"),
    ]
    EFFORT_CHOICES = [
        ("high", "High"),
        ("consistent", "Consistent"),
        ("developing", "Developing"),
        ("low", "Low"),
    ]

    report_card = models.ForeignKey(ReportCard, on_delete=models.CASCADE, related_name="entries")
    subject = models.CharField(max_length=100)
    class_section = models.ForeignKey(
        ClassSection, on_delete=models.SET_NULL, null=True, blank=True, related_name="report_entries"
    )
    achievement = models.CharField(max_length=1, choices=ACHIEVEMENT_CHOICES, blank=True)
    effort = models.CharField(max_length=20, choices=EFFORT_CHOICES, blank=True)
    comment = models.TextField(blank=True)
    teacher_name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_report_card_entries"
        ordering = ["subject"]
        constraints = [
            models.UniqueConstraint(
                fields=["report_card", "subject"], name="uniq_entry_per_subject"
            )
        ]

    def __str__(self):
        return f"{self.report_card_id} · {self.subject}: {self.achievement}"


class ReportCardDocument(BaseModel):
    """
    Immutable, tamper-evident published artifact of a report card. Generated at
    publish time from a frozen snapshot; `content_hash` (SHA-256 of the canonical
    snapshot) proves it has not been altered. There is no API to update or delete
    a document — re-publishing creates a new `version`, retaining prior ones.
    Legal record of what was issued to the family (with parent sign-off).
    """

    report_card = models.ForeignKey(ReportCard, on_delete=models.CASCADE, related_name="documents")
    version = models.PositiveSmallIntegerField(default=1)
    content_hash = models.CharField(max_length=64)
    snapshot = models.JSONField(default=dict)
    pdf_bytes = models.BinaryField()
    published_by = models.CharField(max_length=255, blank=True)
    acknowledged_by = models.CharField(max_length=255, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_report_card_documents"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["report_card", "version"], name="uniq_reportcard_document_version"
            )
        ]

    def verify(self) -> bool:
        """Recompute the hash from the stored snapshot — True if untampered."""
        from products.cyed.reporting.documents import content_hash

        return content_hash(self.snapshot) == self.content_hash

    def __str__(self):
        return f"ReportCardDocument v{self.version} ({self.report_card_id})"
