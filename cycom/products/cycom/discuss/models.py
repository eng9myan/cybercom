from django.db import models

from platform.common.models import BaseModel


class Channel(BaseModel):
    TYPE_CHOICES = [
        ("channel", "Channel"),
        ("dm", "Direct Message"),
        ("group", "Group"),
    ]

    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="channel")
    topic = models.CharField(max_length=255, blank=True)
    member_count = models.PositiveIntegerField(default=0)
    last_interest_dt = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_discuss_channels"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Message(BaseModel):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="messages")
    author = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_discuss_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author}: {self.body[:40]}"
