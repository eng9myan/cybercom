"""
CyIdentity Celery tasks. ADR-0001 (Celery) + ADR-0017 lifecycle automation.
"""

from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from platform.cyidentity.services import SessionService

logger = logging.getLogger("cybercom.cyidentity.tasks")


@shared_task(name="cyidentity.expire_break_glass")
def expire_break_glass_task() -> int:
    """Expire any active break-glass records past their expires_at."""
    from platform.cyidentity.services import BreakGlassService

    return BreakGlassService().expire_due()


@shared_task(name="cyidentity.enforce_idle_timeout")
def enforce_idle_timeout_task() -> int:
    """Revoke sessions idle longer than IDLE_THRESHOLD_SECONDS."""
    return SessionService().enforce_idle_timeout()


@shared_task(name="cyidentity.rotate_client_secret")
def rotate_client_secret_task(client_id: str, created_by: str = "") -> dict:
    """Rotate a single client's secret. Returns {client_id, secret_id, expires_at}."""
    from platform.cyidentity.models import ApplicationClient
    from platform.cyidentity.services import ClientService

    client = ApplicationClient.objects.get(client_id=client_id)
    row, cleartext = ClientService().rotate_secret(client, created_by=created_by)
    return {
        "client_id": client.client_id,
        "secret_id": str(row.id),
        "secret_hint": row.secret_hint,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "rotated_at": timezone.now().isoformat(),
    }
