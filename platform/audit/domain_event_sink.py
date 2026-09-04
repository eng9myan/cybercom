"""
Canonical domain-event -> audit-trail bridge (canonical-data-model-v1.md §5.1).

Every `core_domain_events` row the relay drains is also written to the tamper-
evident audit chain via `AuditService`. This is the first in-process consumer
of the canonical event bus: it lets an event type drop its legacy
`platform.events.OutboxEvent` dual-write and rely on `core_domain_events` +
this sink for its audit footprint.

Registered from `AuditConfig.ready()`.
"""
from __future__ import annotations

import logging

from platform.canonical.events import subscribe

log = logging.getLogger("platform.audit.domain_event_sink")

_CATEGORY_BY_PREFIX = {
    "cymed.patient": "clinical",
    "cymed.encounter": "clinical",
    "cymed.consent": "clinical",
    "cymed.referral": "clinical",
    "cymed.network_referral": "clinical",
    "cymed.document": "clinical",
    "cycom.invoice": "financial",
    "cycom.journal": "financial",
    "cycom.payment": "financial",
}


def _category_for(event_type: str) -> str:
    for prefix, cat in _CATEGORY_BY_PREFIX.items():
        if event_type.startswith(prefix):
            return cat
    return "system"


@subscribe("*")
def record_domain_event(event) -> None:
    from platform.audit.services import AuditService

    try:
        AuditService().record(
            action=event.event_type,
            action_verb="emit",
            resource_type=event.aggregate_type,
            resource_id=str(event.aggregate_id),
            tenant_id=event.tenant_id,
            actor_user_id=str(event.created_by) if event.created_by else "",
            category=_category_for(event.event_type),
            correlation_id=str(event.id),
            payload=event.payload,
        )
    except Exception:  # pragma: no cover - the relay must not stall on audit
        log.exception("failed to audit domain event %s", event.event_type)
