from django.db import models

from platform.common.models import BaseModel


class ImagingResultView(BaseModel):
    REPORT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("preliminary", "Preliminary"),
        ("final", "Final"),
        ("amended", "Amended"),
        ("corrected", "Corrected"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    cymed_imaging_result_id = models.UUIDField(db_index=True)
    imaging_center_id = models.UUIDField(db_index=True)
    imaging_center_name = models.CharField(max_length=255)
    order_number = models.CharField(max_length=100, blank=True)
    accession_number = models.CharField(max_length=100, blank=True, db_index=True)
    study_date = models.DateField(null=True, blank=True)
    modality = models.CharField(max_length=30)
    body_part = models.CharField(max_length=100, blank=True)
    study_description = models.CharField(max_length=500, blank=True)
    report_status = models.CharField(
        max_length=20,
        choices=REPORT_STATUS_CHOICES,
        default="pending",
    )
    radiologist_name = models.CharField(max_length=255, blank=True)
    report_summary = models.TextField(blank=True)
    report_url = models.URLField(max_length=2000, blank=True)
    has_critical_finding = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True, db_index=True)
    fhir_imaging_study_id = models.CharField(max_length=255, blank=True, db_index=True)
    dicom_study_instance_uid = models.CharField(max_length=255, blank=True)
    viewer_url = models.URLField(max_length=2000, blank=True)

    class Meta:
        db_table = "cymed_portal_imaging_results"
        indexes = [
            models.Index(
                fields=["account_id", "modality", "study_date"],
                name="imaging_results_acct_mod_date_idx",
            ),
            models.Index(
                fields=["patient_id", "report_status"],
                name="imaging_results_patient_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.modality} — {self.study_description or self.body_part} ({self.report_status})"
        )


class ImagingStudyMetadata(BaseModel):
    imaging_result = models.ForeignKey(
        ImagingResultView,
        on_delete=models.CASCADE,
        related_name="series",
    )
    series_number = models.PositiveSmallIntegerField()
    series_description = models.CharField(max_length=255, blank=True)
    modality = models.CharField(max_length=30)
    instance_count = models.PositiveSmallIntegerField(default=0)
    series_instance_uid = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_portal_imaging_series"

    def __str__(self):
        return (
            f"Series {self.series_number} — {self.series_description or self.modality} "
            f"({self.instance_count} instances)"
        )


class ImagingReportAccess(BaseModel):
    ACCESS_TYPE_CHOICES = [
        ("view_report", "View Report"),
        ("download_report", "Download Report"),
        ("view_images", "View Images"),
        ("share", "Share"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    imaging_result = models.ForeignKey(
        ImagingResultView,
        on_delete=models.CASCADE,
        related_name="access_log",
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default="view_report",
    )
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_portal_imaging_access"
        ordering = ["-accessed_at"]

    def __str__(self):
        return f"{self.get_access_type_display()} — {self.imaging_result} at {self.accessed_at}"


class ImagingShareLink(BaseModel):
    SHARE_TYPE_CHOICES = [
        ("report_only", "Report Only"),
        ("images_and_report", "Images and Report"),
    ]

    imaging_result = models.ForeignKey(
        ImagingResultView,
        on_delete=models.CASCADE,
        related_name="share_links",
    )
    account_id = models.UUIDField(db_index=True)
    share_token = models.CharField(max_length=255, unique=True, db_index=True)
    share_type = models.CharField(
        max_length=20,
        choices=SHARE_TYPE_CHOICES,
        default="report_only",
    )
    shared_with_name = models.CharField(max_length=255, blank=True)
    valid_until = models.DateTimeField()
    access_count = models.PositiveIntegerField(default=0)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_portal_imaging_share_links"

    def __str__(self):
        return (
            f"Share link ({self.get_share_type_display()}) for "
            f"{self.imaging_result} (token: {self.share_token[:8]}...)"
        )
