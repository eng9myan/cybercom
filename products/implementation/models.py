from django.db import models
from platform.common.models import BaseModel


METHODOLOGY_CHOICES = [
    ("activate", "Activate"),
    ("agile", "Agile"),
    ("waterfall", "Waterfall"),
    ("hybrid", "Hybrid"),
]

PROJECT_STATUS_CHOICES = [
    ("not_started", "Not Started"),
    ("discovery", "Discovery"),
    ("design", "Design"),
    ("build", "Build"),
    ("test", "Test"),
    ("cutover", "Cutover"),
    ("go_live", "Go-Live"),
    ("hypercare", "Hypercare"),
    ("closed", "Closed"),
]

MILESTONE_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("delayed", "Delayed"),
]

TASK_PRIORITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

TASK_STATUS_CHOICES = [
    ("open", "Open"),
    ("in_progress", "In Progress"),
    ("review", "Review"),
    ("done", "Done"),
    ("blocked", "Blocked"),
]

CHECKLIST_TYPE_CHOICES = [
    ("pre_cutover", "Pre-Cutover"),
    ("cutover_day", "Cutover Day"),
    ("post_cutover", "Post-Cutover"),
    ("go_live_verification", "Go-Live Verification"),
]

ISSUE_TYPE_CHOICES = [
    ("bug", "Bug"),
    ("question", "Question"),
    ("training", "Training"),
    ("performance", "Performance"),
    ("data", "Data"),
]

SEVERITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]


class ImplementationProject(BaseModel):
    class Meta:
        app_label = "cybercom_implementation"
        db_table = "cybercom_impl_project"

    customer_id = models.UUIDField(db_index=True)
    customer_name = models.CharField(max_length=200)
    project_code = models.CharField(max_length=50, unique=True)
    methodology = models.CharField(max_length=20, choices=METHODOLOGY_CHOICES)
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default="not_started")
    phase = models.CharField(max_length=50, blank=True)
    start_date = models.DateField(null=True, blank=True)
    go_live_date = models.DateField(null=True, blank=True)
    assigned_pm_id = models.UUIDField(null=True, blank=True)
    contracted_hours = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)
    consumed_hours = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer_name} — {self.project_code} ({self.status})"


class ProjectMilestone(BaseModel):
    class Meta:
        app_label = "cybercom_implementation"
        db_table = "cybercom_impl_milestone"

    project = models.ForeignKey(
        ImplementationProject,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    milestone_name = models.CharField(max_length=200)
    phase = models.CharField(max_length=50, blank=True)
    target_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=MILESTONE_STATUS_CHOICES, default="pending")
    deliverable_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.milestone_name} ({self.status})"


class ProjectTask(BaseModel):
    class Meta:
        app_label = "cybercom_implementation"
        db_table = "cybercom_impl_task"

    project = models.ForeignKey(
        ImplementationProject,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    task_name = models.CharField(max_length=200)
    task_category = models.CharField(max_length=100, blank=True)
    assigned_to_id = models.UUIDField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=TASK_PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default="open")
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.task_name} ({self.status})"


class CutoverChecklist(BaseModel):
    class Meta:
        app_label = "cybercom_implementation"
        db_table = "cybercom_impl_cutover_checklist"

    project = models.ForeignKey(
        ImplementationProject,
        on_delete=models.CASCADE,
        related_name="cutover_checklists",
    )
    checklist_name = models.CharField(max_length=200)
    checklist_type = models.CharField(max_length=30, choices=CHECKLIST_TYPE_CHOICES)
    items = models.JSONField(default=list)
    completed_items = models.JSONField(default=list)
    completed_by_id = models.UUIDField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.checklist_name} ({self.checklist_type})"


class HypercareLog(BaseModel):
    class Meta:
        app_label = "cybercom_implementation"
        db_table = "cybercom_impl_hypercare_log"

    project = models.ForeignKey(
        ImplementationProject,
        on_delete=models.CASCADE,
        related_name="hypercare_logs",
    )
    log_date = models.DateField()
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    description = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.issue_type} — {self.log_date} ({self.severity})"


class MethodologyTemplate(BaseModel):
    class Meta:
        app_label = "cybercom_implementation"
        db_table = "cybercom_impl_methodology_template"

    name = models.CharField(max_length=200)
    template_code = models.CharField(max_length=50, unique=True)
    methodology = models.CharField(max_length=20, choices=METHODOLOGY_CHOICES)
    description = models.TextField(blank=True)
    phase_count = models.PositiveIntegerField(default=0)
    task_templates = models.JSONField(default=list)
    milestone_templates = models.JSONField(default=list)
    estimated_weeks = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.template_code})"
