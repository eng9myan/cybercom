from django.db import models

from platform.common.models import BaseModel


class HealthTimeline(BaseModel):
    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    timeline_name = models.CharField(max_length=200, default="My Health Timeline")
    start_date = models.DateField(null=True, blank=True)
    total_events = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymed_portal_health_timelines"
        unique_together = [("tenant_id", "patient_id")]

    def __str__(self):
        return f"{self.timeline_name} — patient {self.patient_id}"


class HealthTimelineEvent(BaseModel):
    EVENT_TYPE_CHOICES = [
        ("appointment", "Appointment"),
        ("lab_result", "Lab Result"),
        ("imaging", "Imaging"),
        ("prescription", "Prescription"),
        ("hospitalization", "Hospitalization"),
        ("vaccination", "Vaccination"),
        ("diagnosis", "Diagnosis"),
        ("procedure", "Procedure"),
        ("telemedicine", "Telemedicine"),
        ("note", "Note"),
    ]

    timeline = models.ForeignKey(
        HealthTimeline,
        on_delete=models.CASCADE,
        related_name="events",
    )
    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    provider_name = models.CharField(max_length=255, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)
    event_date = models.DateField(db_index=True)
    source_id = models.UUIDField(null=True, blank=True)
    source_type = models.CharField(max_length=50, blank=True)
    is_pinned = models.BooleanField(default=False)
    attachments = models.JSONField(default=list)

    class Meta:
        db_table = "cymed_portal_timeline_events"
        indexes = [
            models.Index(
                fields=["timeline", "event_date"],
                name="timeline_events_timeline_date_idx",
            ),
            models.Index(
                fields=["account_id", "event_type"],
                name="timeline_events_acct_type_idx",
            ),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title} on {self.event_date}"


class PatientJourney(BaseModel):
    JOURNEY_TYPE_CHOICES = [
        ("chronic_condition", "Chronic Condition"),
        ("surgical", "Surgical"),
        ("maternity", "Maternity"),
        ("cancer_care", "Cancer Care"),
        ("rehabilitation", "Rehabilitation"),
        ("preventive", "Preventive"),
        ("general", "General"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("paused", "Paused"),
        ("discontinued", "Discontinued"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    journey_name = models.CharField(max_length=200)
    journey_type = models.CharField(max_length=20, choices=JOURNEY_TYPE_CHOICES)
    primary_diagnosis = models.CharField(max_length=255, blank=True)
    icd11_code = models.CharField(max_length=20, blank=True)
    start_date = models.DateField()
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    care_team = models.JSONField(default=list)
    goals = models.JSONField(default=list)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_portal_patient_journeys"
        indexes = [
            models.Index(
                fields=["account_id", "status"],
                name="patient_journeys_acct_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.journey_name} ({self.get_journey_type_display()}) — {self.get_status_display()}"
        )


class HealthMilestone(BaseModel):
    MILESTONE_TYPE_CHOICES = [
        ("diagnosis", "Diagnosis"),
        ("treatment_start", "Treatment Start"),
        ("surgery", "Surgery"),
        ("first_chemo", "First Chemotherapy"),
        ("remission", "Remission"),
        ("discharge", "Discharge"),
        ("goal_achieved", "Goal Achieved"),
        ("custom", "Custom"),
    ]

    journey = models.ForeignKey(
        PatientJourney,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPE_CHOICES)
    milestone_date = models.DateField()
    is_achieved = models.BooleanField(default=False)
    achieved_at = models.DateTimeField(null=True, blank=True)
    is_shared = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_portal_health_milestones"
        indexes = [
            models.Index(
                fields=["journey", "is_achieved"],
                name="health_milestones_journey_achieved_idx",
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_milestone_type_display()}) on {self.milestone_date}"


class CareEpisode(BaseModel):
    EPISODE_TYPE_CHOICES = [
        ("inpatient", "Inpatient"),
        ("outpatient", "Outpatient"),
        ("emergency", "Emergency"),
        ("telemedicine", "Telemedicine"),
        ("home_care", "Home Care"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    journey = models.ForeignKey(
        PatientJourney,
        on_delete=models.SET_NULL,
        related_name="episodes",
        null=True,
        blank=True,
    )
    episode_type = models.CharField(max_length=20, choices=EPISODE_TYPE_CHOICES)
    facility_name = models.CharField(max_length=255)
    facility_id = models.UUIDField(null=True, blank=True)
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    primary_diagnosis = models.CharField(max_length=255, blank=True)
    icd11_code = models.CharField(max_length=20, blank=True)
    attending_physician = models.CharField(max_length=255, blank=True)
    discharge_summary = models.TextField(blank=True)
    follow_up_instructions = models.TextField(blank=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    cymed_admission_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_portal_care_episodes"
        indexes = [
            models.Index(
                fields=["account_id", "episode_type", "admission_date"],
                name="care_episodes_acct_type_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.get_episode_type_display()} at {self.facility_name} from {self.admission_date}"
        )
