from django.db import models

from platform.common.models import BaseModel

REPORT_STATUSES = [
    ("draft", "Draft"),
    ("preliminary", "Preliminary"),
    ("final", "Final"),
    ("amended", "Amended"),
    ("addended", "Addended"),
]


class ReportTemplate(BaseModel):
    class Meta:
        app_label = "img_reporting"
        db_table = "cymed_img_report_templates"

    name = models.CharField(max_length=255)
    modality = models.CharField(max_length=20)
    body_part = models.CharField(max_length=100, blank=True)
    subspecialty = models.CharField(max_length=100, blank=True)
    template_text = models.TextField()
    findings_template = models.TextField(blank=True)
    impression_template = models.TextField(blank=True)
    is_structured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class RadiologyReport(BaseModel):
    class Meta:
        app_label = "img_reporting"
        db_table = "cymed_img_reports"

    order_item = models.OneToOneField(
        "img_orders.ImagingOrderItem", on_delete=models.CASCADE, related_name="report"
    )
    patient_id = models.UUIDField(db_index=True)
    radiologist_id = models.UUIDField()
    report_template = models.ForeignKey(
        "img_reporting.ReportTemplate", null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(
        max_length=30, choices=REPORT_STATUSES, default="draft", db_index=True
    )
    technique = models.TextField(blank=True)
    clinical_indication = models.TextField(blank=True)
    comparison_studies = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    impression = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    ai_assistance_used = models.BooleanField(default=False)
    dictated_at = models.DateTimeField(null=True, blank=True)
    transcribed_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.UUIDField(null=True, blank=True)
    word_count = models.PositiveIntegerField(default=0)
    report_tat_minutes = models.PositiveIntegerField(null=True, blank=True)
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Report {self.id} — {self.status}"


class RadiologyFinding(BaseModel):
    class Meta:
        app_label = "img_reporting"
        db_table = "cymed_img_findings"

    SEVERITY_CHOICES = [
        ("normal", "Normal"),
        ("minor", "Minor"),
        ("moderate", "Moderate"),
        ("severe", "Severe"),
        ("critical", "Critical"),
    ]

    report = models.ForeignKey(
        "img_reporting.RadiologyReport",
        on_delete=models.CASCADE,
        related_name="structured_findings",
    )
    finding_code = models.CharField(max_length=100, blank=True)  # SNOMED via TerminologyService
    body_region = models.CharField(max_length=100, blank=True)
    laterality = models.CharField(max_length=20, blank=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True)
    is_incidental = models.BooleanField(default=False)
    follow_up_recommended = models.BooleanField(default=False)
    follow_up_timeframe = models.CharField(max_length=100, blank=True)
    size_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    location_detail = models.TextField(blank=True)

    def __str__(self):
        return f"Finding {self.id} — {self.severity}"


class RadiologyImpression(BaseModel):
    report = models.ForeignKey(
        "img_reporting.RadiologyReport",
        on_delete=models.CASCADE,
        related_name="structured_impressions",
    )
    impression_number = models.PositiveSmallIntegerField(default=1)
    impression_text = models.TextField()
    icd11_code = models.CharField(max_length=20, blank=True)  # via TerminologyService
    snomed_code = models.CharField(max_length=20, blank=True)  # via TerminologyService
    is_primary = models.BooleanField(default=False)

    class Meta:
        app_label = "img_reporting"
        db_table = "cymed_img_impressions"
        ordering = ["impression_number"]


class CriticalFinding(BaseModel):
    class Meta:
        app_label = "img_reporting"
        db_table = "cymed_img_critical_findings"

    report = models.ForeignKey(
        "img_reporting.RadiologyReport", on_delete=models.CASCADE, related_name="critical_findings"
    )
    finding_description = models.TextField()
    snomed_code = models.CharField(max_length=20, blank=True)
    severity = models.CharField(
        max_length=20, choices=[("urgent", "Urgent"), ("emergent", "Emergent")], default="urgent"
    )
    notification_status = models.CharField(
        max_length=30,
        choices=[
            ("pending", "Pending"),
            ("notified", "Notified"),
            ("acknowledged", "Acknowledged"),
            ("completed", "Completed"),
        ],
        default="pending",
        db_index=True,
    )
    notified_clinician_id = models.UUIDField(null=True, blank=True)
    notification_method = models.CharField(max_length=30, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    read_back_verified = models.BooleanField(default=False)
    escalated = models.BooleanField(default=False)

    def __str__(self):
        return f"Critical {self.severity} — {self.notification_status}"


class StructuredReport(BaseModel):
    class Meta:
        app_label = "img_reporting"
        db_table = "cymed_img_structured_reports"

    report = models.OneToOneField("img_reporting.RadiologyReport", on_delete=models.CASCADE)
    report_schema = models.CharField(
        max_length=100, blank=True
    )  # e.g. "RADS", "PI-RADS", "TI-RADS"
    schema_version = models.CharField(max_length=20, blank=True)
    score = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=50, blank=True)
    structured_data = models.JSONField(default=dict)
    dicom_sr_uid = models.CharField(max_length=255, blank=True)


class ReportAmendment(BaseModel):
    class Meta:
        app_label = "img_reporting"
        db_table = "cymed_img_report_amendments"

    original_report = models.ForeignKey(
        "img_reporting.RadiologyReport", on_delete=models.CASCADE, related_name="amendments"
    )
    amended_by = models.UUIDField()
    amendment_reason = models.TextField()
    previous_findings = models.TextField()
    previous_impression = models.TextField()
    new_findings = models.TextField()
    new_impression = models.TextField()
    amendment_date = models.DateTimeField(auto_now_add=True)
    is_significant = models.BooleanField(default=False)

    def __str__(self):
        return f"Amendment to {self.original_report_id}"
