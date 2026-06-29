from django.db import models

from platform.common.models import BaseModel


class ProviderResultView(BaseModel):
    RESULT_TYPE_CHOICES = [
        ("laboratory", "Laboratory"),
        ("imaging", "Imaging"),
        ("pathology", "Pathology"),
        ("microbiology", "Microbiology"),
        ("cardiology", "Cardiology"),
        ("pulmonary", "Pulmonary"),
        ("other", "Other"),
    ]
    RESULT_STATUS_CHOICES = [
        ("preliminary", "Preliminary"),
        ("final", "Final"),
        ("corrected", "Corrected"),
        ("amended", "Amended"),
        ("cancelled", "Cancelled"),
    ]

    patient_id = models.UUIDField(db_index=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    result_type = models.CharField(max_length=30, choices=RESULT_TYPE_CHOICES)
    result_source_id = models.UUIDField()
    result_source_type = models.CharField(max_length=50)
    result_name = models.CharField(max_length=255)
    result_date = models.DateField(db_index=True)
    result_status = models.CharField(max_length=20, choices=RESULT_STATUS_CHOICES, default="final")
    is_critical = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by_provider_id = models.UUIDField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    ordering_provider_id = models.UUIDField(db_index=True, null=True, blank=True)
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True)
    result_summary = models.TextField(blank=True)
    loinc_code = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "cymed_prov_results"
        indexes = [
            models.Index(fields=["tenant_id", "patient_id", "result_type"]),
            models.Index(fields=["tenant_id", "ordering_provider_id", "is_reviewed"]),
        ]

    def __str__(self):
        return f"{self.result_name} ({self.result_type}) — {self.result_date}"


class ResultTrend(BaseModel):
    patient_id = models.UUIDField(db_index=True)
    test_code = models.CharField(max_length=100, db_index=True)
    test_name = models.CharField(max_length=255)
    loinc_code = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    datapoints = models.JSONField(default=list)
    reference_range_low = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    reference_range_high = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )

    class Meta:
        db_table = "cymed_prov_result_trends"
        unique_together = [("tenant_id", "patient_id", "test_code")]

    def __str__(self):
        return f"{self.test_name} trend — patient {self.patient_id}"


class CriticalResultAlert(BaseModel):
    ALERT_TYPE_CHOICES = [
        ("critical_value", "Critical Value"),
        ("panic_value", "Panic Value"),
        ("abnormal_flag", "Abnormal Flag"),
        ("delta_check", "Delta Check"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("acknowledged", "Acknowledged"),
        ("escalated", "Escalated"),
        ("resolved", "Resolved"),
    ]

    result = models.ForeignKey(
        ProviderResultView,
        on_delete=models.CASCADE,
        related_name="critical_alerts",
    )
    patient_id = models.UUIDField(db_index=True)
    alerted_provider_id = models.UUIDField(db_index=True)
    alerted_provider_name = models.CharField(max_length=255)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    result_value = models.CharField(max_length=255)
    normal_range = models.CharField(max_length=255, blank=True)
    clinical_significance = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_critical_alerts"

    def __str__(self):
        return f"{self.alert_type} for {self.alerted_provider_name} ({self.status})"


class ResultAcknowledgement(BaseModel):
    ACTION_TAKEN_CHOICES = [
        ("noted", "Noted"),
        ("ordered_follow_up", "Ordered Follow-Up"),
        ("contacted_patient", "Contacted Patient"),
        ("consulted_specialist", "Consulted Specialist"),
        ("no_action_required", "No Action Required"),
        ("other", "Other"),
    ]

    result = models.ForeignKey(
        ProviderResultView,
        on_delete=models.CASCADE,
        related_name="acknowledgements",
    )
    provider_id = models.UUIDField()
    provider_name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=100)
    action_taken = models.CharField(max_length=30, choices=ACTION_TAKEN_CHOICES)
    action_notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_result_acks"

    def __str__(self):
        return f"{self.provider_name} — {self.action_taken} for result {self.result_id}"
