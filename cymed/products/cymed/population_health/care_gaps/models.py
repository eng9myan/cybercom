"""
CyMed Population Health — Care Gaps
Covers: CareGap, CareGapRule, CareGapRecommendation, CareGapResolution
Terminology: ICD-11 and LOINC codes resolved via TerminologyService (not stored locally).
"""

from django.db import models

from platform.common.models import BaseModel

GAP_TYPE_CHOICES = [
    ("screening", "Screening"),
    ("vaccination", "Vaccination"),
    ("follow_up", "Follow Up"),
    ("medication_adherence", "Medication Adherence"),
    ("lab_test", "Lab Test"),
    ("imaging", "Imaging"),
    ("preventive", "Preventive"),
    ("chronic_monitoring", "Chronic Monitoring"),
    ("dental", "Dental"),
    ("mental_health", "Mental Health"),
]

GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
    ("all", "All"),
]


class CareGap(BaseModel):
    """An identified gap in care for a specific patient."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
        ("in_progress", "In Progress"),
        ("waived", "Waived"),
        ("declined", "Declined"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    SOURCE_CHOICES = [
        ("automated", "Automated"),
        ("manual", "Manual"),
        ("registry", "Registry"),
        ("external", "External"),
    ]

    patient_id = models.UUIDField(db_index=True)
    gap_type = models.CharField(max_length=30, choices=GAP_TYPE_CHOICES)
    gap_description = models.CharField(max_length=500)
    icd11_code = models.CharField(max_length=20, blank=True)
    loinc_code = models.CharField(max_length=30, blank=True)
    due_date = models.DateField(null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)
    next_service_due = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    identified_by_rule_id = models.UUIDField(null=True, blank=True)
    assigned_provider_id = models.UUIDField(null=True, blank=True)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default="automated")

    class Meta:
        db_table = "cymed_ph_gap_care_gaps"

    def __str__(self):
        return f"{self.gap_type} — patient {self.patient_id} [{self.status}]"


class CareGapRule(BaseModel):
    """A rule that triggers automatic identification of care gaps."""

    rule_name = models.CharField(max_length=200)
    rule_code = models.CharField(max_length=50, unique=True)
    gap_type = models.CharField(max_length=30, choices=GAP_TYPE_CHOICES)
    description = models.TextField(blank=True)
    criteria = models.JSONField(default=dict)
    recommendation = models.TextField(blank=True)
    frequency_days = models.PositiveIntegerField(null=True, blank=True)
    applies_to_conditions = models.JSONField(default=list)
    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    applies_to_gender = models.CharField(
        max_length=10, blank=True, choices=GENDER_CHOICES, default="all"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_ph_gap_rules"

    def __str__(self):
        return f"{self.rule_code} — {self.rule_name}"


class CareGapRecommendation(BaseModel):
    """A clinical recommendation attached to a care gap."""

    care_gap = models.ForeignKey(CareGap, on_delete=models.CASCADE, related_name="recommendations")
    recommendation_text = models.TextField()
    recommended_by_provider_id = models.UUIDField(null=True, blank=True)
    recommendation_date = models.DateField(auto_now_add=True)
    target_date = models.DateField(null=True, blank=True)
    loinc_code = models.CharField(max_length=30, blank=True)
    service_type = models.CharField(max_length=100, blank=True)
    is_ai_generated = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_ph_gap_recommendations"

    def __str__(self):
        return f"Recommendation for gap {self.care_gap_id}"


class CareGapResolution(BaseModel):
    """Records how and when a care gap was resolved."""

    RESOLUTION_TYPE_CHOICES = [
        ("completed", "Completed"),
        ("waived", "Waived"),
        ("declined", "Declined"),
        ("transferred", "Transferred"),
        ("auto_closed", "Auto Closed"),
    ]

    care_gap = models.ForeignKey(CareGap, on_delete=models.CASCADE, related_name="resolutions")
    resolved_by_user_id = models.UUIDField()
    resolution_date = models.DateField()
    resolution_type = models.CharField(max_length=20, choices=RESOLUTION_TYPE_CHOICES)
    resolution_notes = models.TextField(blank=True)
    service_date = models.DateField(null=True, blank=True)
    encounter_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_ph_gap_resolutions"

    def __str__(self):
        return f"{self.resolution_type} — gap {self.care_gap_id} on {self.resolution_date}"
