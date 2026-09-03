from django.db import models

from platform.common.models import BaseModel


class Project(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_project_projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Task(BaseModel):
    STAGE_CHOICES = [
        ("backlog", "Backlog"),
        ("in_progress", "In Progress"),
        ("review", "Review"),
        ("done", "Done"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.CharField(max_length=255, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="backlog")
    allocated_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    effective_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    priority = models.CharField(max_length=20, default="normal")
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cycom_project_tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.stage})"
