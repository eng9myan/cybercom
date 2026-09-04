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

import logging
import uuid

from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

from platform.canonical.models import DomainEvent

logger = logging.getLogger("platform.canonical.relay")


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


def _resolve_publisher():
    path = getattr(settings, "DOMAIN_EVENT_PUBLISHER", None)
    return import_string(path) if path else None


def relay(limit: int = 500, *, dry_run: bool = False) -> int:
    """Publish up to `limit` unpublished events and stamp `published_at`.
    Returns the number sent (0 on a dry run). Shared by the management command
    and the celery task. With no `settings.DOMAIN_EVENT_PUBLISHER` it logs each
    event so a dev / CI run does not back the table up."""
    publisher = _resolve_publisher()
    events = list(unpublished(limit=limit))
    if dry_run:
        for e in events:
            logger.info("would publish %s <%s:%s>", e.event_type, e.aggregate_type, e.aggregate_id)
        return 0
    sent = 0
    for e in events:
        if publisher:
            publisher(e)
        else:
            logger.info("domain-event %s %s %s", e.event_type, e.aggregate_type, e.aggregate_id)
        e.published_at = timezone.now()
        e.save(update_fields=["published_at"])
        sent += 1
    return sent


def _as_uuid(value):
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
