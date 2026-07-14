"""
CyMed Laboratory â€” Result Management
Covers: LabResult, ResultValue, ReferenceRange, ResultInterpretation,
        CriticalResult, ResultCorrection, ResultApproval
Full validation â†’ verification â†’ approval workflow with delta checks.
"""

from django.db import models

from platform.common.models import BaseModel


class ResultStatus(models.TextChoices):
    PENDING = "pending", "Pending Entry"
    PARTIAL = "partial", "Partial Results"
    RESULTED = "resulted", "All Resulted"
    VERIFIED = "verified", "Verified by Technologist"
    APPROVED = "approved", "Approved by Pathologist/Senior"
    AMENDED = "amended", "Amended"
    CANCELLED = "cancelled", "Cancelled"
    HELD = "held", "On Hold â€” QC Failure"


class InterpretationCode(models.TextChoices):
    NORMAL = "N", "Normal"
    ABNORMAL = "A", "Abnormal"
    HIGH = "H", "High"
    HIGH_HIGH = "HH", "Critical High"
    LOW = "L", "Low"
    LOW_LOW = "LL", "Critical Low"
    POSITIVE = "POS", "Positive"
    NEGATIVE = "NEG", "Negative"
    REACTIVE = "R", "Reactive"
    NON_REACTIVE = "NR", "Non-Reactive"
    INDETERMINATE = "IND", "Indeterminate"
    RESISTANT = "RES", "Resistant"
    INTERMEDIATE = "INT", "Intermediate"
    SUSCEPTIBLE = "SUS", "Susceptible"


class LabResult(BaseModel):
    """Aggregated result record for an order item â€” groups all analyte values."""

    order_item = models.OneToOneField(
        "lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="result"
    )
    specimen = models.ForeignKey(
        "lab_specimens.Specimen",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="results",
    )
    status = models.CharField(
        max_length=20, choices=ResultStatus.choices, default=ResultStatus.PENDING
    )
    has_critical_value = models.BooleanField(default=False)
    has_abnormal_value = models.BooleanField(default=False)
    resulted_by = models.UUIDField(null=True, blank=True)
    resulted_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    method = models.CharField(max_length=100, blank=True)
    instrument_code = models.CharField(max_length=50, blank=True)
    comments = models.TextField(blank=True)
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_lab_results"
        indexes = [models.Index(fields=["tenant_id", "status", "has_critical_value"])]


class ResultValue(BaseModel):
    """Individual analyte measurement within a result set."""

    VALUE_TYPES = [
        ("numeric", "Numeric"),
        ("text", "Text"),
        ("coded", "Coded Value"),
        ("titer", "Titer"),
        ("range", "Range"),
    ]

    result = models.ForeignKey(LabResult, on_delete=models.CASCADE, related_name="values")
    analyte_code = models.CharField(max_length=100)  # internal code
    analyte_name = models.CharField(max_length=255)
    loinc_code = models.CharField(max_length=20, blank=True)  # from TerminologyService
    value_type = models.CharField(max_length=20, choices=VALUE_TYPES, default="numeric")
    value_numeric = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    value_text = models.CharField(max_length=500, blank=True)
    value_coded = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    interpretation = models.CharField(max_length=5, choices=InterpretationCode.choices, blank=True)
    is_critical = models.BooleanField(default=False)
    is_abnormal = models.BooleanField(default=False)
    delta_flag = models.BooleanField(default=False)
    previous_value = models.CharField(max_length=100, blank=True)
    previous_value_date = models.DateField(null=True, blank=True)
    delta_percentage = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    sequence = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_result_values"
        ordering = ["result", "sequence"]


class ReferenceRange(BaseModel):
    """Age/sex/population-specific normal ranges for a test analyte."""

    SEX_CHOICES = [("M", "Male"), ("F", "Female"), ("all", "All")]

    test = models.ForeignKey(
        "lab_orders.LabTest", on_delete=models.CASCADE, related_name="reference_ranges"
    )
    analyte_code = models.CharField(max_length=100, blank=True)
    sex = models.CharField(max_length=5, choices=SEX_CHOICES, default="all")
    age_min_years = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    age_max_years = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    value_low = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    value_high = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    critical_low = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    critical_high = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    text_range = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_lab_reference_ranges"
        indexes = [models.Index(fields=["test", "sex", "age_min_years", "age_max_years"])]


class ResultInterpretation(BaseModel):
    """Narrative or structured interpretation attached to a result value."""

    result_value = models.OneToOneField(
        ResultValue, on_delete=models.CASCADE, related_name="interpretation_note"
    )
    interpretation_text = models.TextField()
    interpretation_method = models.CharField(max_length=100, blank=True)
    generated_by = models.CharField(max_length=50, default="manual")  # manual, cyai, rule
    ai_confidence_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    reviewed_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_result_interpretations"


class CriticalResult(BaseModel):
    """Mandatory notification workflow for life-threatening result values."""

    NOTIFICATION_STATUS = [
        ("pending", "Pending Notification"),
        ("notified", "Notified â€” Acknowledgement Pending"),
        ("acknowledged", "Acknowledged"),
        ("escalated", "Escalated"),
        ("closed", "Closed"),
    ]

    result_value = models.OneToOneField(
        ResultValue, on_delete=models.CASCADE, related_name="critical_alert"
    )
    critical_at = models.DateTimeField(auto_now_add=True)
    notification_status = models.CharField(
        max_length=20, choices=NOTIFICATION_STATUS, default="pending"
    )
    notified_by = models.UUIDField(null=True, blank=True)
    notified_to_id = models.UUIDField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    notification_method = models.CharField(max_length=50, blank=True)  # phone, sms, system
    acknowledgement_name = models.CharField(max_length=255, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    read_back_verified = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_critical_results"
        indexes = [models.Index(fields=["notification_status", "critical_at"])]


class ResultCorrection(BaseModel):
    """Amendment record â€” immutable record of original vs. corrected value."""

    result = models.ForeignKey(LabResult, on_delete=models.CASCADE, related_name="corrections")
    analyte_code = models.CharField(max_length=100)
    original_value = models.CharField(max_length=255)
    corrected_value = models.CharField(max_length=255)
    correction_reason = models.TextField()
    corrected_by = models.UUIDField()
    corrected_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_result_corrections"
        ordering = ["-corrected_at"]


class ResultApproval(BaseModel):
    """Electronic signoff record for result release â€” replaces wet signature."""

    result = models.ForeignKey(LabResult, on_delete=models.CASCADE, related_name="approvals")
    approval_level = models.CharField(max_length=30)  # verification, pathologist, director
    approved_by = models.UUIDField()
    approved_at = models.DateTimeField(auto_now_add=True)
    digital_signature = models.CharField(max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    signature_method = models.CharField(max_length=30, default="pin")  # pin, biometric, token
    comments = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_result_approvals"
        ordering = ["-approved_at"]
