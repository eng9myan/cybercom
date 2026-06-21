"""
Transactional Outbox pattern implementation. ADR-0004: Event-driven architecture.
Services write business records AND outbox events in one atomic transaction.
Debezium CDC reads WAL and publishes to Kafka.
"""
import uuid
from django.db import models
from django.utils import timezone


class OutboxEventStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PUBLISHED = "published", "Published"
    FAILED = "failed", "Failed"


class OutboxEvent(models.Model):
    """
    Transactional outbox table. Written atomically with business records.
    Debezium monitors this table via PostgreSQL WAL CDC.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    topic = models.CharField(max_length=500, db_index=True)
    event_type = models.CharField(max_length=200, db_index=True)
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=OutboxEventStatus.choices,
        default=OutboxEventStatus.PENDING, db_index=True
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "platform_outbox_events"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["topic", "status"]),
        ]

    def __str__(self) -> str:
        return f"OutboxEvent({self.topic}, {self.event_type}, {self.status})"

    def mark_published(self) -> None:
        self.status = OutboxEventStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])

    def mark_failed(self, error: str) -> None:
        self.status = OutboxEventStatus.FAILED
        self.error_message = error
        self.retry_count += 1
        self.save(update_fields=["status", "error_message", "retry_count"])
