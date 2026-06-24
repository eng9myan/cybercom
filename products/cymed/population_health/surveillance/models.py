rom django.db import models
from platform.common.models import BaseModel


CASE_TYPE_CHOICES = [
    ("confirmed", "Confirmed"),
    ("probable", "Probable"),
    ("suspected", "Suspected"),
    ("not_a_case", "Not a Case"),
]

CASE_STATUS_CHOICES = [
    ("open", "Open"),
    ("under_investigation", "Under Investigation"),
    ("closed", "Closed"),
    ("discarded", "Discarded"),
]

OUTBREAK_TYPE_CHOICES = [
    ("epidemic", "Epidemic"),
    ("cluster", "Cluster"),
    ("sporadic", "Sporadic"),
    ("endemic", "Endemic"),
]

OUTBREAK_STATUS_CHOICES = [
    ("active", "Active"),
    ("contained", "Contained"),
    ("resolved", "Resolved"),
    ("monitoring", "Monitoring"),
]

SEVERITY_LEVEL_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

ALERT_LEVEL_CHOICES = [
    ("green", "Green"),
    ("yellow", "Yellow"),
    ("orange", "Orange"),
    ("red", "Red"),
]

EVENT_TYPE_CHOICES = [
    ("disease_surge", "Disease Surge"),
    ("mass_gathering", "Mass Gathering"),
    ("natural_disaster", "Natural Disaster"),
    ("environmental_hazard", "Environmental Hazard"),
    ("food_contamination", "Food Contamination"),
    ("chemical_exposure", "Chemical Exposure"),
    ("vaccination_drive", "Vaccination Drive"),
    ("health_campaign", "Health Campaign"),
    ("other", "Other"),
]

RESPONSE_STATUS_CHOICES = [
    ("planning", "Planning"),
    ("active", "Active"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]

INVESTIGATION_OUTCOME_CHOICES = [
    ("resolved", "Resolved"),
    ("ongoing", "Ongoing"),
    ("referred", "Referred"),
    ("closed", "Closed"),
]


class SurveillanceCase(BaseModel):
    class Meta:
        app_label = "cymed_ph_surveillance"
        db_table = "cymed_ph_surv_cases"

    patient_id = models.UUIDField(db_index=True)
    # ICD-11 code sourced from TerminologyService — no local table
    disease_code = models.CharField(max_length=20)
    disease_name = models.CharField(max_length=200)
    case_type = models.CharField(
        max_length=20, choices=CASE_TYPE_CHOICES, default="suspected"
    )
    case_date = models.DateField()
    reporting_facility_id = models.UUIDField(null=True, blank=True)
    reporting_provider_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=CASE_STATUS_CHOICES, default="open"
    )
    # True when disease requires mandatory reporting to public health authorities
    is_notifiable = models.BooleanField(default=False)
    outbreak_id = models.UUIDField(null=True, blank=True)
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Case {self.disease_code} ({self.case_type}) — {self.case_date}"


class Outbreak(BaseModel):
    class Meta:
        app_label = "cymed_ph_surveillance"
        db_table = "cymed_ph_surv_outbreaks"

    # ICD-11 code sourced from TerminologyService — no local table
    disease_code = models.CharField(max_length=20)
    disease_name = models.CharField(max_length=200)
    outbreak_type = models.CharField(
        max_length=20, choices=OUTBREAK_TYPE_CHOICES, default="cluster"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    geographic_scope = models.CharField(max_length=200, blank=True)
    affected_count = models.PositiveIntegerField(default=0)
    suspected_count = models.PositiveIntegerField(default=0)
    confirmed_count = models.PositiveIntegerField(default=0)
    deaths_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=OUTBREAK_STATUS_CHOICES, default="active"
    )
    severity_level = models.CharField(
        max_length=10, choices=SEVERITY_LEVEL_CHOICES, default="low"
    )
    is_reported_to_authority = models.BooleanField(default=False)

    def __str__(self):
        return f"Outbreak {self.disease_name} ({self.outbreak_type}) — {self.start_date}"


class OutbreakAlert(BaseModel):
    class Meta:
        app_label = "cymed_ph_surveillance"
        db_table = "cymed_ph_surv_outbreak_alerts"

    outbreak = models.ForeignKey(
        Outbreak,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    alert_level = models.CharField(
        max_length=10, choices=ALERT_LEVEL_CHOICES, default="yellow"
    )
    alert_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    issued_by_authority = models.CharField(max_length=200, blank=True)
    recommended_actions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Alert {self.alert_level} for outbreak {self.outbreak_id}"


class PublicHealthEvent(BaseModel):
    class Meta:
        app_label = "cymed_ph_surveillance"
        db_table = "cymed_ph_surv_public_health_events"

    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    event_name = models.CharField(max_length=200)
    event_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    geographic_scope = models.CharField(max_length=200, blank=True)
    severity = models.CharField(
        max_length=10, choices=SEVERITY_LEVEL_CHOICES, default="low"
    )
    response_status = models.CharField(
        max_length=20, choices=RESPONSE_STATUS_CHOICES, default="planning"
    )
    responsible_authority = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.event_name} ({self.event_type}) — {self.event_date}"


class CaseInvestigation(BaseModel):
    class Meta:
        app_label = "cymed_ph_surveillance"
        db_table = "cymed_ph_surv_case_investigations"

    surveillance_case = models.ForeignKey(
        SurveillanceCase,
        on_delete=models.CASCADE,
        related_name="investigations",
    )
    investigator_id = models.UUIDField()
    investigation_date = models.DateField()
    exposure_history = models.TextField(blank=True)
    probable_source = models.CharField(max_length=500, blank=True)
    contacts_identified = models.PositiveIntegerField(default=0)
    contacts_traced = models.PositiveIntegerField(default=0)
    contacts_tested = models.PositiveIntegerField(default=0)
    outcome = models.CharField(
        max_length=30, choices=INVESTIGATION_OUTCOME_CHOICES, default="ongoing"
    )
    findings = models.TextField(blank=True)

    def __str__(self):
        return f"Investigation for case {self.surveillance_case_id} — {self.investigation_date}"
