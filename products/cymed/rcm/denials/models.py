import uuid
from django.db import models
from platform.common.models import BaseModel


class DenialReason(BaseModel):
    CATEGORY_CHOICES = [
        ("eligibility", "Eligibility"),
        ("authorization", "Authorization"),
        ("medical_necessity", "Medical Necessity"),
        ("coding", "Coding"),
        ("documentation", "Documentation"),
        ("duplicate", "Duplicate"),
        ("timely_filing", "Timely Filing"),
        ("network", "Network"),
        ("other", "Other"),
    ]

    denial_code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    common_resolution = models.TextField(blank=True)
    appeal_success_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_rcm_denial_reasons"
        ordering = ["denial_code"]

    def __str__(self):
        return f"{self.denial_code} - {self.description[:60]}"


class Denial(BaseModel):
    CATEGORY_CHOICES = DenialReason.CATEGORY_CHOICES

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_review", "In Review"),
        ("appealing", "Appealing"),
        ("resolved", "Resolved"),
        ("written_off", "Written Off"),
    ]

    ROOT_CAUSE_CHOICES = [
        ("missing_auth", "Missing Authorization"),
        ("wrong_code", "Wrong Code"),
        ("expired_coverage", "Expired Coverage"),
        ("missing_docs", "Missing Documentation"),
        ("wrong_provider", "Wrong Provider"),
        ("other", "Other"),
    ]

    claim_id = models.UUIDField(db_index=True)
    claim_line_id = models.UUIDField(null=True, blank=True)
    patient_id = models.UUIDField(db_index=True)
    insurance_plan_id = models.UUIDField(db_index=True)
    denial_date = models.DateField()
    denial_code = models.CharField(max_length=50)
    denial_category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    denial_description = models.TextField()
    denial_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    root_cause = models.CharField(max_length=30, choices=ROOT_CAUSE_CHOICES, blank=True)
    assigned_to_user_id = models.UUIDField(null=True, blank=True)
    ai_denial_prediction = models.BooleanField(default=False)
    ai_prediction_confidence = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = "cymed_rcm_denial_denials"
        ordering = ["-denial_date", "-created_at"]

    def __str__(self):
        return f"Denial {self.id} | {self.denial_code} | {self.status}"


class Appeal(BaseModel):
    APPEAL_TYPE_CHOICES = [
        ("internal", "Internal"),
        ("external", "External"),
        ("peer_review", "Peer Review"),
        ("administrative", "Administrative"),
        ("legal", "Legal"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("upheld", "Upheld"),
        ("overturned", "Overturned"),
        ("partially_overturned", "Partially Overturned"),
        ("withdrawn", "Withdrawn"),
    ]

    denial = models.ForeignKey(
        Denial, on_delete=models.PROTECT, related_name="appeals"
    )
    appeal_level = models.PositiveSmallIntegerField(default=1)
    appeal_date = models.DateField()
    submitted_by_user_id = models.UUIDField()
    appeal_type = models.CharField(max_length=20, choices=APPEAL_TYPE_CHOICES)
    appeal_reason = models.TextField()
    supporting_documents = models.JSONField(default=list)
    clinical_justification = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    deadline_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_rcm_denial_appeals"
        ordering = ["-appeal_date", "appeal_level"]

    def __str__(self):
        return f"Appeal {self.id} | Level {self.appeal_level} | {self.status}"


class AppealOutcome(BaseModel):
    OUTCOME_CHOICES = [
        ("approved", "Approved"),
        ("partially_approved", "Partially Approved"),
        ("denied", "Denied"),
        ("withdrawn", "Withdrawn"),
    ]

    appeal = models.OneToOneField(
        Appeal, on_delete=models.CASCADE, related_name="outcome"
    )
    outcome_date = models.DateField()
    outcome = models.CharField(max_length=30, choices=OUTCOME_CHOICES)
    recovered_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    outcome_notes = models.TextField(blank=True)
    payer_reference = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "cymed_rcm_denial_appeal_outcomes"
        ordering = ["-outcome_date"]

    def __str__(self):
        return f"Outcome {self.id} | {self.outcome} | Appeal {self.appeal_id}"


class CorrectiveAction(BaseModel):
    ACTION_TYPE_CHOICES = [
        ("resubmit_with_auth", "Resubmit with Authorization"),
        ("add_documentation", "Add Documentation"),
        ("recode", "Recode"),
        ("correct_patient_info", "Correct Patient Info"),
        ("resubmit_in_network", "Resubmit In-Network"),
        ("write_off", "Write Off"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    denial = models.ForeignKey(
        Denial, on_delete=models.CASCADE, related_name="corrective_actions"
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    description = models.TextField()
    assigned_to_user_id = models.UUIDField()
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    class Meta:
        db_table = "cymed_rcm_denial_corrective_actions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"CorrectiveAction {self.id} | {self.action_type} | {self.status}"
