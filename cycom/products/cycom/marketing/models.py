from django.db import models

from platform.common.models import BaseModel


class Campaign(BaseModel):
    TYPE_CHOICES = [
        ("email", "Email Blast"),
        ("sms", "SMS Alert"),
        ("newsletter", "Newsletter"),
    ]
    STATE_CHOICES = [
        ("draft", "Draft"),
        ("in_queue", "Scheduled"),
        ("sending", "Sending"),
        ("done", "Sent"),
    ]

    name = models.CharField(max_length=255)
    campaign_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="email")
    target = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default="draft")
    sent = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)
    open_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    click_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    body = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_marketing_campaigns"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.state})"
