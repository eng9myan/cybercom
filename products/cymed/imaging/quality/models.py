from django.db import models
from platform.common.models import BaseModel


class QualityAudit(BaseModel):
    class Meta:
        app_label = "img_quality"
        db_table = "cymed_img_quality_audits"

    report = models.ForeignKey("img_reporting.RadiologyReport", on_delete=models.CASCADE, related_name="quality_audits")
    auditor_id = models.UUIDField()
    audit_type = models.CharField(max_length=30, choices=[
        ("peer_review", "Peer Review"), ("clinical_audit", "Clinical Audit"),
        ("random_audit", "Random Audit"), ("targeted_audit", "Targeted Audit"),
    ], default="peer_review")
    score = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    feedback = models.TextField(blank=True)
    discrepancy_level = models.CharField(max_length=20, choices=[
        ("none", "None"), ("minor", "Minor"), ("major", "Major"), ("critical", "Critical"),
    ], default="none")
    action_required = models.BooleanField(default=False)
    action_description = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Audit {self.id} — {self.audit_type}"


class ImagingQualityMetric(BaseModel):
    class Meta:
        app_label = "img_quality"
        db_table = "cymed_img_quality_metrics"
        unique_together = [("modality", "metric_date")]

    modality = models.ForeignKey("img_worklist.Modality", on_delete=models.CASCADE)
    metric_date = models.DateField(db_index=True)
    repeat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rejection_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    patient_dose_avg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    patient_dose_unit = models.CharField(max_length=20, blank=True)
    total_studies = models.PositiveIntegerField(default=0)
    repeated_studies = models.PositiveIntegerField(default=0)
    reason_breakdown = models.JSONField(default=dict)
    within_dose_reference = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.modality.code} — {self.metric_date}"


class RadiationDoseRecord(BaseModel):
    class Meta:
        app_label = "img_quality"
        db_table = "cymed_img_dose_records"

    order_item = models.OneToOneField("img_orders.ImagingOrderItem", on_delete=models.CASCADE, related_name="dose_record")
    patient_id = models.UUIDField(db_index=True)
    modality = models.CharField(max_length=20)
    effective_dose_msv = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    ctdivol = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    dlp = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    dap = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    kvp = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    mas = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    ssde = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    dose_report_uid = models.CharField(max_length=255, blank=True)
    exceeds_drp = models.BooleanField(default=False)

    def __str__(self):
        return f"Dose {self.order_item_id} — {self.modality}"


class AccreditationRecord(BaseModel):
    class Meta:
        app_label = "img_quality"
        db_table = "cymed_img_accreditation"

    accreditation_body = models.CharField(max_length=100)
    accreditation_type = models.CharField(max_length=100)
    certificate_number = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    modality_types = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=[
        ("active", "Active"), ("expired", "Expired"), ("suspended", "Suspended"),
    ], default="active")
    next_review_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.accreditation_body} — {self.accreditation_type}"
