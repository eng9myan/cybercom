"""
Notification delivery.

In-app messages are stored and shown in the portal immediately. Email and SMS
go through the provider seam in `providers.py`; push and WhatsApp have no
adapter yet and say so.

The rule that governs this whole module: **a message is only ever `sent` once a
provider has acknowledged it.** Marking an external message delivered when
nothing was transmitted is a duty-of-care defect, not a harmless placeholder —
the school believes a guardian was told their child is absent, and holds a
record saying so. Every failure path below therefore lands on `failed` with the
reason attached, and never on `sent`.
"""

import logging
import os

from django.utils import timezone

from products.cyed.notifications.providers import (
    NotificationProviderError,
    UnconfiguredProvider,
    get_provider,
)

logger = logging.getLogger(__name__)

_EXTERNAL = {"email", "sms", "push", "whatsapp"}
# Channels with a working adapter. `whatsapp` is routed here so enabling it
# produces an honest failure rather than a silent drop.
_SUPPORTED = {"email", "sms", "push"}


def _provider_enabled(channel: str) -> bool:
    return os.environ.get(f"CYED_NOTIFY_{channel.upper()}_ENABLED") == "1"


def deliver(notification):
    """
    Attempt delivery; update status/sent_at/error. Returns the notification.

    An external channel that is not enabled stays `queued` — honestly not sent,
    and visible as such — rather than failing. That distinction matters: queued
    is a configuration state a school chose, failed is something that went
    wrong and needs looking at.
    """
    if notification.channel == "in_app":
        notification.status = "sent"
        notification.sent_at = timezone.now()
    elif not _provider_enabled(notification.channel):
        notification.status = "queued"
    else:
        try:
            receipt = _send_external(notification)
        except (NotificationProviderError, UnconfiguredProvider) as exc:
            notification.status = "failed"
            notification.error = str(exc)[:255]
            # Logged without the body: a failed absence alert names a child and
            # says they are missing, and log aggregators are not the place for it.
            logger.warning(
                "Notification %s failed on %s: %s",
                notification.id, notification.channel, exc,
            )
        else:
            notification.status = "sent"
            notification.sent_at = timezone.now()
            if receipt and receipt.reference:
                notification.provider_reference = receipt.reference[:120]
                notification.provider = receipt.provider[:40]

    notification.save(update_fields=[
        "status", "sent_at", "error", "provider", "provider_reference", "updated_at",
    ])
    return notification


def _send_external(notification):
    """Hand the message to the configured provider for its channel."""
    channel = notification.channel
    if channel not in _SUPPORTED:
        raise UnconfiguredProvider(
            f"CYED_NOTIFY_{channel.upper()}_ENABLED is set, but CyEd has no {channel} "
            f"adapter yet. Messages on this channel cannot be delivered."
        )

    provider = get_provider(channel)

    if channel == "push":
        return _send_push(notification, provider)

    if channel == "sms":
        recipient = (notification.recipient_phone or "").strip()
        if not recipient:
            raise NotificationProviderError(
                "No phone number on record for this recipient."
            )
        # SMS has no subject line; prefixing it keeps the message intelligible
        # when it arrives as a bare text with no context.
        body = f"{notification.subject}\n\n{notification.body}".strip()
        return provider.send(to=recipient, body=body)

    recipient = (notification.recipient_email or "").strip()
    if not recipient:
        raise NotificationProviderError(
            "No email address on record for this recipient."
        )
    return provider.send(
        to=recipient, subject=notification.subject, body=notification.body
    )


def _send_push(notification, provider):
    """
    Push to every device this recipient has registered.

    A person with a phone and a laptop has two subscriptions and both should
    buzz. Succeeding if *any* device took it: requiring all of them would mark
    a delivered message failed because an old laptop's subscription expired.

    Dead subscriptions are retired as they are found. A browser that dropped
    the subscription returns 404 or 410 forever, and retrying it every time is
    how a queue fills with work that can never succeed.
    """
    from django.utils import timezone as _timezone

    from products.cyed.notifications.models import PushDevice
    from products.cyed.notifications.providers import DEAD_SUBSCRIPTION_CODES

    recipient = (notification.recipient_email or "").strip()
    if not recipient:
        raise NotificationProviderError("No account on record to push to.")

    devices = list(PushDevice.objects.filter(
        tenant_id=notification.tenant_id, owner_email__iexact=recipient, is_active=True
    ))
    if not devices:
        raise NotificationProviderError(
            "This recipient has no registered device. Ask them to enable notifications."
        )

    receipt, errors = None, []
    for device in devices:
        try:
            receipt = provider.send(
                device=device, subject=notification.subject, body=notification.body
            ) or receipt
            device.last_used_at = _timezone.now()
            device.save(update_fields=["last_used_at", "updated_at"])
        except NotificationProviderError as exc:
            message = str(exc)
            errors.append(message)
            if any(code in message for code in DEAD_SUBSCRIPTION_CODES):
                device.is_active = False
                device.failed_at = _timezone.now()
                device.failure_reason = message[:255]
                device.save(update_fields=[
                    "is_active", "failed_at", "failure_reason", "updated_at",
                ])

    if receipt is None:
        raise NotificationProviderError("; ".join(errors)[:255] or "No device accepted the push.")
    return receipt


def retry_failed(tenant_id, *, limit=200):
    """
    Re-attempt failed messages — a provider outage should not need a human to
    re-send every absence alert by hand.

    Bounded, and only touches `failed`: a `queued` message is waiting on
    configuration, not on a retry.
    """
    from products.cyed.notifications.models import Notification

    rows = Notification.objects.filter(
        tenant_id=tenant_id, status="failed", channel__in=_SUPPORTED
    ).order_by("created_at")[:limit]

    attempted = recovered = 0
    for notification in rows:
        attempted += 1
        deliver(notification)
        if notification.status == "sent":
            recovered += 1
    return {"attempted": attempted, "recovered": recovered}
