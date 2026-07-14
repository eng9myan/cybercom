from django.db import models

from platform.common.models import BaseModel


class ClinicalRound(BaseModel):
    ROUND_TYPE_CHOICES = [
        ("ward", "Ward"),
        ("icu", "ICU"),
        ("multidisciplinary", "Multidisciplinary"),
        ("virtual", "Virtual"),
        ("nursing", "Nursing"),
        ("pharmacy", "Pharmacy"),
        ("administrative", "Administrative"),
    ]
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    round_type = models.CharField(max_length=30, choices=ROUND_TYPE_CHOICES)
    round_name = models.CharField(max_length=255, blank=True)
    unit_id = models.UUIDField(db_index=True, null=True, blank=True)
    unit_name = models.CharField(max_length=255, blank=True)
    attending_provider_id = models.UUIDField()
    attending_name = models.CharField(max_length=255)
    round_date = models.DateField(db_index=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    patient_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_rounds"

    def __str__(self):
        return f"{self.round_type} round — {self.round_date} ({self.attending_name})"


class RoundTeam(BaseModel):
    ROLE_CHOICES = [
        ("attending", "Attending"),
        ("resident", "Resident"),
        ("intern", "Intern"),
        ("nurse", "Nurse"),
        ("pharmacist", "Pharmacist"),
        ("therapist", "Therapist"),
        ("social_worker", "Social Worker"),
        ("student", "Student"),
        ("observer", "Observer"),
    ]

    round = models.ForeignKey(
        ClinicalRound,
        on_delete=models.CASCADE,
        related_name="team_members",
    )
    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(null=True, blank=True)
    is_present = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_prov_round_teams"

    def __str__(self):
        return f"{self.provider_name} ({self.role}) — round {self.round_id}"


class RoundChecklist(BaseModel):
    round = models.ForeignKey(
        ClinicalRound,
        on_delete=models.CASCADE,
        related_name="checklists",
    )
    patient_id = models.UUIDField(db_index=True)
    patient_name = models.CharField(max_length=255, blank=True)
    bed_number = models.CharField(max_length=50, blank=True)
    checklist_items = models.JSONField(default=list)
    completed_items = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_round_checklists"

    def __str__(self):
        return f"Checklist for patient {self.patient_id} — round {self.round_id}"


class RoundFinding(BaseModel):
    FINDING_TYPE_CHOICES = [
        ("clinical_observation", "Clinical Observation"),
        ("vital_sign_concern", "Vital Sign Concern"),
        ("medication_issue", "Medication Issue"),
        ("imaging_result", "Imaging Result"),
        ("lab_result", "Lab Result"),
        ("care_plan_update", "Care Plan Update"),
        ("discharge_planning", "Discharge Planning"),
        ("other", "Other"),
    ]
    SEVERITY_CHOICES = [
        ("routine", "Routine"),
        ("notable", "Notable"),
        ("urgent", "Urgent"),
        ("critical", "Critical"),
    ]

    round = models.ForeignKey(
        ClinicalRound,
        on_delete=models.CASCADE,
        related_name="findings",
    )
    patient_id = models.UUIDField(db_index=True)
    finding_type = models.CharField(max_length=40, choices=FINDING_TYPE_CHOICES)
    finding_text = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="routine")
    recorded_by_provider_id = models.UUIDField()
    recorded_by_name = models.CharField(max_length=255)
    requires_action = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_prov_round_findings"

    def __str__(self):
        return f"{self.finding_type} ({self.severity}) — round {self.round_id}"


class RoundAction(BaseModel):
    ACTION_TYPE_CHOICES = [
        ("order_placed", "Order Placed"),
        ("task_created", "Task Created"),
        ("note_written", "Note Written"),
        ("referral_sent", "Referral Sent"),
        ("medication_adjusted", "Medication Adjusted"),
        ("discharge_initiated", "Discharge Initiated"),
        ("family_notified", "Family Notified"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    round = models.ForeignKey(
        ClinicalRound,
        on_delete=models.CASCADE,
        related_name="actions",
    )
    finding = models.ForeignKey(
        RoundFinding,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    patient_id = models.UUIDField(db_index=True)
    action_type = models.CharField(max_length=40, choices=ACTION_TYPE_CHOICES)
    action_description = models.TextField()
    assigned_to_provider_id = models.UUIDField(null=True, blank=True)
    assigned_to_name = models.CharField(max_length=255, blank=True)
    due_by = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_round_actions"

    def __str__(self):
        return f"{self.action_type} ({self.status}) — round {self.round_id}"
