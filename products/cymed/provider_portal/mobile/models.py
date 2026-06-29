from django.db import models

from platform.common.models import BaseModel


class ProviderMobileDevice(BaseModel):
    DEVICE_TYPE_CHOICES = [
        ("ios", "iOS"),
        ("android", "Android"),
        ("tablet", "Tablet"),
    ]

    provider_id = models.UUIDField(db_index=True)
    provider_workspace_id = models.UUIDField(null=True, blank=True)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES)
    push_token = models.CharField(max_length=512, blank=True, db_index=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    platform_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_trusted = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "cymed_provider_mobile"
        db_table = "cymed_prov_mobile_devices"

    def __str__(self):
        return f"{self.device_name} ({self.device_type}) — provider {self.provider_id}"


class MobileSession(BaseModel):
    device = models.ForeignKey(
        ProviderMobileDevice,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    provider_id = models.UUIDField(db_index=True)
    session_token = models.CharField(max_length=512, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    context_patient_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    biometric_verified = models.BooleanField(default=False)

    class Meta:
        app_label = "cymed_provider_mobile"
        db_table = "cymed_prov_mobile_sessions"

    def __str__(self):
        return f"Session {self.session_token[:12]}… — provider {self.provider_id}"


class MobilePreferences(BaseModel):
    HOME_TAB_CHOICES = [
        ("dashboard", "Dashboard"),
        ("patient_lists", "Patient Lists"),
        ("tasks", "Tasks"),
        ("results", "Results"),
        ("messages", "Messages"),
    ]

    device = models.OneToOneField(
        ProviderMobileDevice,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    provider_id = models.UUIDField()
    home_tab = models.CharField(max_length=20, choices=HOME_TAB_CHOICES, default="dashboard")
    push_critical_results = models.BooleanField(default=True)
    push_task_alerts = models.BooleanField(default=True)
    push_messages = models.BooleanField(default=True)
    push_approval_requests = models.BooleanField(default=True)
    biometric_login = models.BooleanField(default=True)
    quick_action_1 = models.CharField(max_length=100, blank=True)
    quick_action_2 = models.CharField(max_length=100, blank=True)
    offline_patient_ids = models.JSONField(default=list)

    class Meta:
        app_label = "cymed_provider_mobile"
        db_table = "cymed_prov_mobile_preferences"

    def __str__(self):
        return f"Preferences for device {self.device_id}"


class MobilePushNotification(BaseModel):
    NOTIFICATION_TYPE_CHOICES = [
        ("critical_result", "Critical Result"),
        ("task_assigned", "Task Assigned"),
        ("task_overdue", "Task Overdue"),
        ("message_received", "Message Received"),
        ("approval_required", "Approval Required"),
        ("round_starting", "Round Starting"),
        ("credential_expiry", "Credential Expiry"),
        ("schedule_change", "Schedule Change"),
        ("patient_deterioration", "Patient Deterioration"),
        ("system_alert", "System Alert"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    provider_id = models.UUIDField(db_index=True)
    device_id = models.UUIDField(db_index=True, null=True, blank=True)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    action_type = models.CharField(max_length=100, blank=True)
    action_id = models.UUIDField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="normal")
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    source_type = models.CharField(max_length=100, blank=True)
    source_id = models.UUIDField(null=True, blank=True)

    class Meta:
        app_label = "cymed_provider_mobile"
        db_table = "cymed_prov_mobile_notifications"
        indexes = [
            models.Index(
                fields=["tenant_id", "provider_id", "is_read", "created_at"],
                name="cymed_prov_notif_idx",
            ),
        ]

    def __str__(self):
        return f"{self.title} — {self.notification_type} ({self.priority})"
