from django.db import models

from platform.common.models import BaseModel


class TaskType(models.TextChoices):
    LAB_FOLLOW_UP = "lab_follow_up", "Lab Follow-Up"
    IMAGING_FOLLOW_UP = "imaging_follow_up", "Imaging Follow-Up"
    MEDICATION_REVIEW = "medication_review", "Medication Review"
    PATIENT_CALLBACK = "patient_callback", "Patient Callback"
    REFERRAL = "referral", "Referral"
    DISCHARGE_PLANNING = "discharge_planning", "Discharge Planning"
    CARE_COORDINATION = "care_coordination", "Care Coordination"
    DOCUMENTATION = "documentation", "Documentation"
    CRITICAL_RESULT_REVIEW = "critical_result_review", "Critical Result Review"
    ORDER_REVIEW = "order_review", "Order Review"
    WOUND_CARE = "wound_care", "Wound Care"
    VITAL_SIGNS = "vital_signs", "Vital Signs"
    BLOOD_GLUCOSE = "blood_glucose", "Blood Glucose"
    MEDICATION_ADMINISTRATION = "medication_administration", "Medication Administration"
    CUSTOM = "custom", "Custom"


class TaskPriority(models.TextChoices):
    ROUTINE = "routine", "Routine"
    URGENT = "urgent", "Urgent"
    STAT = "stat", "STAT"
    CRITICAL = "critical", "Critical"


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    ESCALATED = "escalated", "Escalated"


class AssignmentType(models.TextChoices):
    PRIMARY = "primary", "Primary"
    COLLABORATOR = "collaborator", "Collaborator"
    OBSERVER = "observer", "Observer"


class ClinicalTask(BaseModel):
    task_type = models.CharField(max_length=50, choices=TaskType.choices)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    patient_id = models.UUIDField(db_index=True, null=True, blank=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.ROUTINE,
    )
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    assigned_to_provider_id = models.UUIDField(db_index=True)
    assigned_to_type = models.CharField(max_length=50)
    created_by_provider_id = models.UUIDField()
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by_provider_id = models.UUIDField(null=True, blank=True)
    escalated_to_provider_id = models.UUIDField(null=True, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    source_type = models.CharField(max_length=100, blank=True)
    source_id = models.UUIDField(null=True, blank=True)
    unit_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task({self.title} / {self.status})"


class TaskAssignment(BaseModel):
    task = models.ForeignKey(
        ClinicalTask,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    provider_id = models.UUIDField(db_index=True)
    provider_type = models.CharField(max_length=50)
    assigned_by = models.UUIDField()
    assignment_type = models.CharField(max_length=20, choices=AssignmentType.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_prov_task_assignments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"TaskAssignment(task={self.task_id} provider={self.provider_id})"


class TaskComment(BaseModel):
    task = models.ForeignKey(
        ClinicalTask,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author_provider_id = models.UUIDField()
    author_name = models.CharField(max_length=255)
    comment_text = models.TextField()
    is_system_comment = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_prov_task_comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"TaskComment(task={self.task_id} by={self.author_name})"


class TaskEscalation(BaseModel):
    task = models.ForeignKey(
        ClinicalTask,
        on_delete=models.CASCADE,
        related_name="escalations",
    )
    escalated_by_provider_id = models.UUIDField()
    escalated_to_provider_id = models.UUIDField()
    escalation_reason = models.TextField()
    previous_priority = models.CharField(max_length=20)
    new_priority = models.CharField(max_length=20)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_task_escalations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"TaskEscalation(task={self.task_id})"
