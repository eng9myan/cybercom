from django.db import models

from platform.common.models import BaseModel


class LabResultView(BaseModel):
    RESULT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("partial", "Partial"),
        ("final", "Final"),
        ("corrected", "Corrected"),
        ("amended", "Amended"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    cymed_lab_result_id = models.UUIDField(db_index=True)
    lab_id = models.UUIDField(db_index=True)
    lab_name = models.CharField(max_length=255)
    order_number = models.CharField(max_length=100, blank=True)
    test_name = models.CharField(max_length=500)
    test_code = models.CharField(max_length=100, blank=True)
    loinc_code = models.CharField(max_length=20, blank=True)
    specimen_type = models.CharField(max_length=100, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    resulted_at = models.DateTimeField(null=True, blank=True)
    result_status = models.CharField(
        max_length=20,
        choices=RESULT_STATUS_CHOICES,
        default="pending",
    )
    result_summary = models.TextField(blank=True)
    is_critical = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    pdf_url = models.URLField(max_length=2000, blank=True)
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True, db_index=True)

    class Meta:
        db_table = "cymed_portal_lab_results"
        indexes = [
            models.Index(
                fields=["account_id", "result_status", "resulted_at"],
                name="lab_results_acct_status_date_idx",
            ),
            models.Index(
                fields=["patient_id", "is_critical"],
                name="lab_results_patient_critical_idx",
            ),
        ]

    def __str__(self):
        return f"{self.test_name} ({self.result_status}) — {self.lab_name}"


class LabResultTrend(BaseModel):
    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    test_code = models.CharField(max_length=100, db_index=True)
    test_name = models.CharField(max_length=500)
    loinc_code = models.CharField(max_length=20, blank=True)
    datapoints = models.JSONField(default=list)
    unit = models.CharField(max_length=50, blank=True)
    reference_range_low = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    reference_range_high = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymed_portal_lab_trends"
        unique_together = [("tenant_id", "patient_id", "test_code")]

    def __str__(self):
        return f"{self.test_name} trend for patient {self.patient_id}"


class CriticalResultAcknowledgement(BaseModel):
    ACTION_CHOICES = [
        ("contacted_provider", "Contacted Provider"),
        ("scheduled_appointment", "Scheduled Appointment"),
        ("went_to_er", "Went to ER"),
        ("no_action", "No Action"),
        ("other", "Other"),
    ]

    lab_result = models.ForeignKey(
        LabResultView,
        on_delete=models.CASCADE,
        related_name="acknowledgements",
    )
    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    action_taken = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        default="no_action",
    )
    notes = models.TextField(blank=True)
    notified_provider_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_portal_critical_ack"

    def __str__(self):
        return f"Acknowledgement for {self.lab_result} — {self.get_action_taken_display()}"


class LabResultShareLink(BaseModel):
    lab_result = models.ForeignKey(
        LabResultView,
        on_delete=models.CASCADE,
        related_name="share_links",
    )
    account_id = models.UUIDField(db_index=True)
    share_token = models.CharField(max_length=255, unique=True, db_index=True)
    shared_with_name = models.CharField(max_length=255, blank=True)
    shared_with_email = models.EmailField(blank=True)
    valid_until = models.DateTimeField()
    access_count = models.PositiveIntegerField(default=0)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_portal_lab_share_links"

    def __str__(self):
        return f"Share link for {self.lab_result} (token: {self.share_token[:8]}...)"
