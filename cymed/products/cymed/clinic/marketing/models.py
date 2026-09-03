"""Marketing automation — appointment reminders, recall campaigns."""
from django.db import models

from platform.common.models import BaseModel, SoftDeleteMixin


class Campaign(BaseModel, SoftDeleteMixin):
    KIND = [
        ("appointment_reminder", "Appointment reminder"),
        ("recall_annual_checkup", "Annual checkup recall"),
        ("recall_lab_repeat", "Lab repeat reminder"),
        ("promo_service", "Service promotion"),
        ("birthday", "Birthday greeting"),
        ("no_show_win_back", "No-show win-back"),
        ("post_visit_survey", "Post-visit survey"),
    ]
    CHANNEL = [("sms", "SMS"), ("email", "Email"), ("whatsapp", "WhatsApp"), ("push", "Push")]
    STATUS = [("draft", "Draft"), ("scheduled", "Scheduled"),
              ("running", "Running"), ("completed", "Completed"),
              ("paused", "Paused")]

    tenant_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=40, choices=KIND)
    channel = models.CharField(max_length=20, choices=CHANNEL)
    subject = models.CharField(max_length=200, blank=True)
    body_template = models.TextField(help_text="Supports {{patient_name}}, {{clinic_name}}, {{appt_time}}")
    audience_filter = models.JSONField(default=dict, blank=True)  # Segment definition
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft", db_index=True)

    class Meta:
        db_table = "cymed_clinic_campaigns"


class CampaignSend(BaseModel):
    STATUS = [("queued", "Queued"), ("sent", "Sent"), ("delivered", "Delivered"),
              ("failed", "Failed"), ("opened", "Opened"), ("clicked", "Clicked")]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="sends")
    patient_profile_id = models.UUIDField(db_index=True)
    channel_address = models.CharField(max_length=200)  # phone or email
    payload = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default="queued", db_index=True)
    provider_reference = models.CharField(max_length=200, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_clinic_campaign_sends"
        indexes = [models.Index(fields=["campaign", "status"])]
