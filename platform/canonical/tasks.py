"""
Canonical-layer Celery tasks.

`relay_domain_events` drains the `core_domain_events` outbox to the broker.
Register it on a short beat (every ~30s) alongside the other platform periodic
tasks:

    CELERY_BEAT_SCHEDULE["canonical.relay_domain_events"] = {
        "task": "canonical.relay_domain_events",
        "schedule": 30.0,
    }
"""
from __future__ import annotations

import logging

from celery import shared_task

from platform.canonical.events import relay

log = logging.getLogger("platform.canonical.relay")


@shared_task(name="canonical.relay_domain_events")
def relay_domain_events(limit: int = 500) -> int:
    sent = relay(limit=limit)
    if sent:
        log.info("canonical relay published %s domain events", sent)
    return sent
