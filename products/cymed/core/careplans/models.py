from django.db import models
from django.utils import timezone
from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient
from products.cymed.core.providers.models import Provider

class CarePlan(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="careplans")
    status = models.CharField(max_length=30, choices=[
        ("draft", "Draft"), ("active", "Active"), ("suspended", "Suspended"), ("completed", "Completed")
    ], default="active")
    intent = models.CharField(max_length=30, choices=[
        ("proposal", "Proposal"), ("plan", "Plan"), ("order", "Order")
    ], default="plan")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    period_start = models.DateTimeField(default=timezone.now)
    period_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_careplans"
        ordering = ["-period_start"]

    def __str__(self) -> str:
        return f"{self.title} ({self.patient.mrn})"


class CareGoal(BaseModel):
    careplan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="goals")
    description = models.TextField()
    status = models.CharField(max_length=30, choices=[
        ("proposed", "Proposed"), ("active", "Active"), ("achieved", "Achieved"), ("failed", "Failed")
    ], default="active")
    target_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_careplan_goals"


class CareTask(BaseModel):
    careplan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=[
        ("ready", "Ready"), ("in_progress", "In Progress"), ("completed", "Completed"), ("cancelled", "Cancelled")
    ], default="ready")
    assigned_provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "cymed_careplan_tasks"


class CareIntervention(BaseModel):
    careplan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="interventions")
    intervention_type = models.CharField(max_length=100)  # e.g., "physiotherapy", "dietary"
    description = models.TextField()

    class Meta:
        db_table = "cymed_careplan_interventions"


class CarePathway(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_careplan_pathways"


class CareTeam(BaseModel):
    careplan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="care_teams")
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(Provider, db_table="cymed_careteam_members")

    class Meta:
        db_table = "cymed_careteams"
