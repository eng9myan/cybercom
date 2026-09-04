"""
Canonical domain-event emission (canonical-data-model-v1.md §5.1).

`emit()` writes one `DomainEvent` row inside the caller's transaction — the
transactional-outbox pattern. A relay worker (`manage.py relay_domain_events`,
or a Debezium/CDC pipe in production) moves unpublished rows to the broker;
consumers are analytics, audit, the integration hub, and flavor engines.

This is the canonical successor to `platform.events.OutboxEvent`. During the
migration window a service may dual-write both; new code should emit here.
"""
from __future__ import annotations

import uuid

from platform.canonical.models import DomainEvent


def emit(
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id,
    payload: dict | None = None,
    schema_version: int = 1,
    tenant_id=None,
) -> DomainEvent:
    """Record a domain event. `tenant_id` falls back to the ambient tenant
    context via `BaseModel.save()`; pass it explicitly from a job / task."""
    kwargs = dict(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=_as_uuid(aggregate_id),
        payload=payload or {},
        schema_version=schema_version,
    )
    if tenant_id is not None:
        kwargs["tenant_id"] = tenant_id
    return DomainEvent.objects.create(**kwargs)


def unpublished(limit: int | None = None):
    """The relay's work queue — oldest unpublished events first."""
    qs = DomainEvent.objects.filter(published_at__isnull=True).order_by("occurred_at")
    return qs[:limit] if limit else qs


def _as_uuid(value):
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
