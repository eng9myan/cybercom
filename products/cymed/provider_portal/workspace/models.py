from django.db import models

from platform.common.models import BaseModel


class ProviderType(models.TextChoices):
    PHYSICIAN = "physician", "Physician"
    CONSULTANT = "consultant", "Consultant"
    RESIDENT = "resident", "Resident"
    NURSE = "nurse", "Nurse"
    CHARGE_NURSE = "charge_nurse", "Charge Nurse"
    PHARMACIST = "pharmacist", "Pharmacist"
    CLINICAL_PHARMACIST = "clinical_pharmacist", "Clinical Pharmacist"
    RADIOLOGIST = "radiologist", "Radiologist"
    LAB_TECHNOLOGIST = "lab_technologist", "Lab Technologist"
    MICROBIOLOGIST = "microbiologist", "Microbiologist"
    PATHOLOGIST = "pathologist", "Pathologist"
    THERAPIST = "therapist", "Therapist"
    CARE_COORDINATOR = "care_coordinator", "Care Coordinator"
    ADMINISTRATOR = "administrator", "Administrator"


class DeviceType(models.TextChoices):
    DESKTOP = "desktop", "Desktop"
    TABLET = "tablet", "Tablet"
    MOBILE = "mobile", "Mobile"


class ProviderWorkspace(BaseModel):
    provider_id = models.UUIDField(db_index=True)
    provider_type = models.CharField(max_length=30, choices=ProviderType.choices)
    cyidentity_user_id = models.UUIDField()
    is_active = models.BooleanField(default=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    preferred_specialty = models.CharField(max_length=255, blank=True)
    home_unit_id = models.UUIDField(null=True, blank=True)
    home_unit_name = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=100, default="UTC")

    class Meta:
        db_table = "cymed_prov_workspaces"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Workspace({self.provider_id} / {self.provider_type})"


class ProviderDashboard(BaseModel):
    workspace = models.OneToOneField(
        ProviderWorkspace,
        on_delete=models.CASCADE,
        related_name="dashboard",
    )
    layout_config = models.JSONField(default=dict)
    pinned_patient_ids = models.JSONField(default=list)
    active_patient_list_id = models.UUIDField(null=True, blank=True)
    show_tasks = models.BooleanField(default=True)
    show_results = models.BooleanField(default=True)
    show_messages = models.BooleanField(default=True)
    show_schedule = models.BooleanField(default=True)
    show_approvals = models.BooleanField(default=True)
    show_census = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_prov_dashboards"

    def __str__(self):
        return f"Dashboard({self.workspace_id})"


class ProviderPreferences(BaseModel):
    workspace = models.OneToOneField(
        ProviderWorkspace,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    default_note_template = models.CharField(max_length=255, blank=True)
    smart_phrase_favorites = models.JSONField(default=list)
    result_critical_alert_sound = models.BooleanField(default=True)
    task_notification_push = models.BooleanField(default=True)
    task_notification_email = models.BooleanField(default=True)
    message_notification_push = models.BooleanField(default=True)
    handoff_auto_include_summary = models.BooleanField(default=True)
    ai_suggestions_enabled = models.BooleanField(default=True)
    voice_dictation_enabled = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_prov_preferences"

    def __str__(self):
        return f"Preferences({self.workspace_id})"


class WorkspaceSession(BaseModel):
    workspace = models.ForeignKey(
        ProviderWorkspace,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    session_token = models.CharField(max_length=512, unique=True)
    device_type = models.CharField(max_length=20, choices=DeviceType.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    context_patient_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_sessions"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Session({self.workspace_id} / {self.device_type})"
