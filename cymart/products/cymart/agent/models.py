import uuid

from django.db import models


class AgentMessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class AgentMessage(models.Model):
    """Audit log of the CyMart agent's conversation, scoped per customer.
    Also doubles as the conversation-history source for AgentSession —
    context is rebuilt from these rows rather than trusting a
    client-supplied history array, so a caller can't inject fake
    assistant/tool turns into their own context."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(db_index=True)
    role = models.CharField(max_length=10, choices=AgentMessageRole.choices)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_agent_message"
        ordering = ["created_at"]
