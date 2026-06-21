"""
Base domain event model for CyberCom Python services. ADR-0004.
All domain events extend DomainEvent for Kafka publishing.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DomainEvent:
    """Base class for all CyberCom domain events."""
    event_type: str
    tenant_id: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    correlation_id: str | None = None
    causation_id: str | None = None
    version: int = 1
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "tenantId": self.tenant_id,
            "occurredAt": self.occurred_at,
            "correlationId": self.correlation_id,
            "causationId": self.causation_id,
            "version": self.version,
            "payload": self.payload,
            "metadata": self.metadata,
        }

    @property
    def kafka_topic(self) -> str:
        """Derives Kafka topic from event type. e.g. 'cymed.patient.admitted' → 'cybercom.cymed.patient.admitted'"""
        return f"cybercom.{self.event_type}"
