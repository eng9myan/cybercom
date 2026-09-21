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


class TimesheetEntry(BaseModel):
    """A logged block of work. Rolls up into Task.effective_hours on save/delete."""

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="timesheet_entries", null=True, blank=True
    )
    employee_name = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_project_timesheet_entries"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.employee_name or 'unassigned'} — {self.date} ({self.hours}h)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.task_id:
            self._recalc_task_hours(self.task_id)

    def delete(self, *args, **kwargs):
        task_id = self.task_id
        super().delete(*args, **kwargs)
        if task_id:
            self._recalc_task_hours(task_id)

    @staticmethod
    def _recalc_task_hours(task_id):
        from django.db.models import Sum

        total = (
            TimesheetEntry.objects.filter(task_id=task_id).aggregate(total=Sum("hours"))["total"]
            or 0
        )
        # .update() (not task.save()) — avoids re-triggering Task's own save
        # path for a field it doesn't otherwise own the value of.
        Task.objects.filter(pk=task_id).update(effective_hours=total)
