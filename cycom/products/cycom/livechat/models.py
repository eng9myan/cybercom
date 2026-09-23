import secrets

from django.db import models

from platform.common.models import BaseModel


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


class ChatSession(BaseModel):
    """One visitor's chat, reachable via an unguessable public token — same
    posture as esign's SignRequest, storefront's Cart."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
    ]

    token = models.CharField(max_length=64, unique=True, default=_generate_token, editable=False)
    visitor_name = models.CharField(max_length=255, blank=True)
    visitor_email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")

    class Meta:
        db_table = "cycom_livechat_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Chat {self.token[:8]} ({self.status})"


class ChatMessage(BaseModel):
    SENDER_CHOICES = [
        ("visitor", "Visitor"),
        ("agent", "Agent"),
    ]

    session = models.ForeignKey(ChatSession, related_name="messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    body = models.TextField()

    class Meta:
        db_table = "cycom_livechat_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.body[:30]}"
