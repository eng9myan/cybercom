from django.db import models

from platform.common.models import BaseModel


class Event(BaseModel):
    RECURRENCE_CHOICES = [
        ("none", "None"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    attendees = models.JSONField(default=list, blank=True, help_text="List of attendee emails.")
    linked_model = models.CharField(max_length=100, blank=True)
    linked_id = models.UUIDField(null=True, blank=True)
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default="none")
    organizer = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_calendar_events"
        ordering = ["start_at"]

    def __str__(self):
        return f"{self.title} ({self.start_at:%Y-%m-%d %H:%M})"
