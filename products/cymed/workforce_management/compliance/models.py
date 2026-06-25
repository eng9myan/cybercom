from django.db import models
from platform.common.models import BaseModel


COUNTRY_CODE_CHOICES = [
    ("USA", "United States"),
    ("SAU", "Saudi Arabia"),
    ("JOR", "Jordan"),
    ("ARE", "United Arab Emirates"),
    ("OTHER", "Other"),
]

ACCREDITATION_BODY_CHOICES = [
    ("TJC", "The Joint Commission (TJC)"),
    ("CBAHI", "Saudi Central Board for Accrediting Healthcare Institutions (CBAHI)"),
    ("JCIA", "Joint Commission International Accreditation (JCIA)"),
    ("DHA", "Dubai Health Authority (DHA)"),
    ("DOH", "Department of Health Abu Dhabi (DOH)"),
    ("OTHER", "Other"),
]


class WorkforceComplianceConfig(BaseModel):
    class Meta:
        app_label = "cymed_hwm_compliance"
        db_table = "cymed_hwm_compliance_config"
        unique_together = [["tenant_id", "country_code", "region_code"]]

    country_code = models.CharField(max_length=10, choices=COUNTRY_CODE_CHOICES)
    region_code = models.CharField(max_length=20, default="ALL")

    # Labor rules
    max_weekly_hours = models.PositiveSmallIntegerField(default=48)
    max_consecutive_days = models.PositiveSmallIntegerField(default=6)
    min_rest_hours_between_shifts = models.PositiveSmallIntegerField(default=11)
    overtime_threshold_daily_hours = models.PositiveSmallIntegerField(default=8)

    # Accreditation
    accreditation_body = models.CharField(max_length=20, choices=ACCREDITATION_BODY_CHOICES)
    mandatory_shift_supervisor = models.BooleanField(default=True)
    credential_verification_frequency_days = models.PositiveSmallIntegerField(default=365)

    # California-specific staffing mandate ratios stored as JSON
    ratio_overrides = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Compliance {self.country_code}/{self.region_code} ({self.accreditation_body})"


class RamadanComplianceRule(BaseModel):
    class Meta:
        app_label = "cymed_hwm_compliance"
        db_table = "cymed_hwm_compliance_ramadan"
        unique_together = [["tenant_id", "compliance_config"]]

    compliance_config = models.OneToOneField(
        WorkforceComplianceConfig,
        on_delete=models.CASCADE,
        related_name="ramadan_rule",
    )
    # Reduced hours apply to Muslim employees during Ramadan
    muslim_max_daily_hours = models.PositiveSmallIntegerField(default=6)
    muslim_max_weekly_hours = models.PositiveSmallIntegerField(default=36)
    # Islamic calendar month numbers (Ramadan = 9)
    ramadan_hijri_month = models.PositiveSmallIntegerField(default=9)

    def __str__(self):
        return f"Ramadan Rule — {self.compliance_config}"


class WardRatioConfig(BaseModel):
    class Meta:
        app_label = "cymed_hwm_compliance"
        db_table = "cymed_hwm_compliance_ward_ratio"
        unique_together = [["tenant_id", "compliance_config", "ward_type"]]

    compliance_config = models.ForeignKey(
        WorkforceComplianceConfig,
        on_delete=models.CASCADE,
        related_name="ward_ratios",
    )
    ward_type = models.CharField(max_length=30)
    day_ratio_nurse = models.PositiveSmallIntegerField(default=1)
    day_ratio_patients = models.PositiveSmallIntegerField(default=4)
    night_ratio_nurse = models.PositiveSmallIntegerField(default=1)
    night_ratio_patients = models.PositiveSmallIntegerField(default=6)

    def __str__(self):
        return f"{self.ward_type} ratio — {self.compliance_config}"


class ComplianceAuditLog(BaseModel):
    class Meta:
        app_label = "cymed_hwm_compliance"
        db_table = "cymed_hwm_compliance_audit_log"

    actor_user_id = models.UUIDField(db_index=True)
    actor_role = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=200)
    compliance_data = models.JSONField(default=dict)
    # Cryptographic signature for immutability verification
    signature = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Audit {self.action} by {self.actor_user_id}"
