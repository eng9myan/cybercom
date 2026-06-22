"""
Celery tasks for API Framework. ADR-0030.
"""
import logging
from celery import shared_task
from django.utils import timezone

log = logging.getLogger(__name__)


@shared_task(name="platform.api.deliver_webhook")
def deliver_webhook_task(delivery_id: str) -> dict:
    """Attempt HTTP delivery of a single webhook delivery record."""
    import urllib.request
    import urllib.error
    import json

    from .models import ApiWebhookDelivery, WebhookDeliveryStatus

    try:
        delivery = ApiWebhookDelivery.objects.select_related("webhook").get(id=delivery_id)
    except ApiWebhookDelivery.DoesNotExist:
        log.warning("Webhook delivery %s not found", delivery_id)
        return {"status": "not_found"}

    if delivery.status == WebhookDeliveryStatus.DELIVERED:
        return {"status": "already_delivered"}

    wh = delivery.webhook
    payload_bytes = json.dumps(delivery.payload).encode()
    headers = {
        "Content-Type": "application/json",
        "X-CyberCom-Signature": f"sha256={delivery.signature}",
        "X-CyberCom-Event": delivery.event_type,
        "X-CyberCom-Delivery": str(delivery.id),
        **wh.headers,
    }
    req = urllib.request.Request(wh.target_url, data=payload_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read(4096).decode(errors="replace")
            delivery.mark_delivered(response_code=resp.status, response_body=body)
            return {"status": "delivered", "response_code": resp.status}
    except urllib.error.HTTPError as e:
        body = e.read(1024).decode(errors="replace") if e.fp else ""
        delivery.mark_failed(str(e), response_code=e.code)
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        delivery.mark_failed(str(e))
        return {"status": "failed", "error": str(e)}


@shared_task(name="platform.api.retry_dead_webhooks")
def retry_dead_webhooks_task() -> dict:
    """Re-queue webhook deliveries that are due for retry."""
    from .models import ApiWebhookDelivery, WebhookDeliveryStatus

    now = timezone.now()
    due = ApiWebhookDelivery.objects.filter(
        status=WebhookDeliveryStatus.RETRYING,
        next_retry_at__lte=now,
    ).select_related("webhook")[:100]

    queued = 0
    for delivery in due:
        deliver_webhook_task.delay(str(delivery.id))
        queued += 1

    log.info("Queued %d webhook retries", queued)
    return {"queued": queued}


@shared_task(name="platform.api.reset_rate_limits")
def reset_rate_limits_task() -> dict:
    """Hourly: clear in-memory rate limit windows for burst keys."""
    from .rate_limit import get_rate_limiter
    rl = get_rate_limiter()
    rl.reset_all()
    log.info("Rate limit windows reset")
    return {"status": "ok"}


@shared_task(name="platform.api.aggregate_usage")
def aggregate_usage_task() -> dict:
    """Daily: aggregate ApiUsage into summary buckets (placeholder for analytics pipeline)."""
    from .models import ApiUsage
    from django.db.models import Count, Avg
    since = timezone.now() - __import__("datetime").timedelta(hours=24)
    agg = ApiUsage.objects.filter(timestamp__gte=since).aggregate(
        total=Count("id"),
        avg_latency=Avg("latency_ms"),
    )
    log.info("24h API usage: total=%s avg_latency=%s", agg["total"], agg["avg_latency"])
    return agg


@shared_task(name="platform.api.expire_api_keys")
def expire_api_keys_task() -> dict:
    """Hourly: mark expired ApiKeys."""
    from .models import ApiKey, ApiKeyStatus
    now = timezone.now()
    expired_count = ApiKey.objects.filter(
        status=ApiKeyStatus.ACTIVE,
        expires_at__lt=now,
    ).update(status=ApiKeyStatus.EXPIRED)
    log.info("Marked %d API keys as expired", expired_count)
    return {"expired": expired_count}


@shared_task(name="platform.api.purge_idempotency_keys")
def purge_idempotency_keys_task() -> dict:
    """Hourly: delete expired idempotency keys."""
    from .idempotency import IdempotencyService
    count = IdempotencyService().purge_expired()
    log.info("Purged %d expired idempotency keys", count)
    return {"purged": count}


@shared_task(name="platform.api.disable_failed_webhooks")
def disable_failed_webhooks_task() -> dict:
    """Daily: disable webhooks with too many consecutive dead-letter deliveries."""
    from .models import ApiWebhook, ApiWebhookDelivery, WebhookStatus, WebhookDeliveryStatus
    FAILURE_THRESHOLD = 50
    disabled = 0
    for wh in ApiWebhook.objects.filter(status=WebhookStatus.ACTIVE):
        dead_count = ApiWebhookDelivery.objects.filter(
            webhook=wh, status=WebhookDeliveryStatus.DEAD
        ).count()
        if dead_count >= FAILURE_THRESHOLD:
            wh.disable()
            disabled += 1
            log.warning("Disabled webhook %s — %d dead-letter deliveries", wh.id, dead_count)
    return {"disabled": disabled}
