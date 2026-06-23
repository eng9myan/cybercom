import uuid
from django.db import models
from platform.common.models import BaseModel


class PatientNotification(BaseModel):
    NOTIFICATION_TYPE_CHOICES = [
        ('appointment_confirmed', 'Appointment Confirmed'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_cancelled', 'Appointment Cancelled'),
        ('lab_result_ready', 'Lab Result Ready'),
        ('imaging_result_ready', 'Imaging Result Ready'),
        ('prescription_ready', 'Prescription Ready'),
        ('refill_reminder', 'Refill Reminder'),
        ('invoice_due', 'Invoice Due'),
        ('payment_received', 'Payment Received'),
        ('preauth_approved', 'Preauth Approved'),
        ('preauth_denied', 'Preauth Denied'),
        ('message_received', 'Message Received'),
        ('critical_result', 'Critical Result'),
        ('system_alert', 'System Alert'),
        ('health_reminder', 'Health Reminder'),
        ('wellness_tip', 'Wellness Tip'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    action_url = models.CharField(max_length=500, blank=True)
    action_label = models.CharField(max_length=100, blank=True)
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.UUIDField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    channels_sent = models.JSONField(default=list)

    class Meta:
        db_table = 'cymed_portal_notifications'
        indexes = [
            models.Index(fields=['account_id', 'is_read', 'notification_type']),
            models.Index(fields=['account_id', 'priority', 'created_at']),
        ]

    def __str__(self):
        return f"Notification: {self.title} ({self.notification_type})"


class NotificationPreference(BaseModel):
    account_id = models.UUIDField(unique=True, db_index=True)
    push_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    appointment_notifications = models.BooleanField(default=True)
    lab_notifications = models.BooleanField(default=True)
    prescription_notifications = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    health_tips = models.BooleanField(default=True)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_notification_preferences'

    def __str__(self):
        return f"Notification Preferences for account {self.account_id}"


class NotificationTemplate(BaseModel):
    CHANNEL_CHOICES = [
        ('push', 'Push'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In App'),
    ]

    code = models.CharField(max_length=50, unique=True)
    notification_type = models.CharField(max_length=50)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='push')
    language = models.CharField(max_length=10, default='en')
    title_template = models.CharField(max_length=255)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cymed_portal_notification_templates'

    def __str__(self):
        return f"Template: {self.code} ({self.channel})"


class PushSubscription(BaseModel):
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]

    account_id = models.UUIDField(db_index=True)
    device_id = models.UUIDField(null=True, blank=True)
    push_token = models.CharField(max_length=500, db_index=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='android')
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_push_subscriptions'
        indexes = [
            models.Index(fields=['account_id', 'is_active']),
        ]

    def __str__(self):
        return f"Push Subscription - {self.platform} ({self.account_id})"
