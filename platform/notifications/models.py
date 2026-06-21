"""
Notification channel models. Platform-level, tenant-scoped.
Supports email, SMS, push (FCM/APNs), in-app, webhooks.
"""
import uuid
from django.db import models
from django.utils import timezone
from platform.common.models import BaseModel


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    PUSH = "push", "Push Notification"
    IN_APP = "in_app", "In-App"
    WEBHOOK = "webhook", "Webhook"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    DELIVERED = "delivered", "Delivered"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class NotificationTemplate(BaseModel):
    """Reusable notification template per tenant."""
    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    subject = models.CharField(max_length=500, blank=True)
    body_ar = models.TextField()
    body_en = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_notification_templates"
        unique_together = [("tenant_id", "name", "channel")]

    def __str__(self) -> str:
        return f"Template({self.name}, {self.channel})"


class Notification(BaseModel):
    """Individual notification record."""
    template = models.ForeignKey(
        NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    recipient_id = models.CharField(max_length=255, db_index=True)
    recipient_address = models.CharField(max_length=500)
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    status = models.CharField(
        max_length=20, choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING, db_index=True
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient_id", "status"]),
            models.Index(fields=["status", "scheduled_at"]),
        ]
