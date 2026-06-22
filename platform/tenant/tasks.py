"""
CyberCom Multi-Tenant Framework — Celery Async Tasks.
"""
import logging
from celery import shared_task
from django.utils import timezone

log = logging.getLogger(__name__)


@shared_task(name="tenant.check_subscription_expiry")
def check_subscription_expiry_task():
    """Suspend tenants with expired subscriptions."""
    from platform.tenant.models import Tenant, TenantSubscription, TenantStatus
    from platform.tenant.services import TenantLifecycleService

    now = timezone.now()
    expired = TenantSubscription.objects.filter(
        is_active=True,
        ends_at__lt=now,
        tenant__status=TenantStatus.ACTIVE,
    ).select_related("tenant")

    svc = TenantLifecycleService()
    count = 0
    for sub in expired:
        try:
            svc.suspend(sub.tenant, reason="subscription_expired", by="system")
            sub.is_active = False
            sub.save(update_fields=["is_active", "updated_at"])
            count += 1
        except Exception:
            log.exception("Failed to suspend tenant %s for expired subscription", sub.tenant.slug)

    log.info("check_subscription_expiry: suspended %d tenants", count)
    return count


@shared_task(name="tenant.expire_feature_flags")
def expire_feature_flags_task():
    """Disable feature flags past their expiry."""
    from platform.tenant.models import TenantFeatureFlag

    now = timezone.now()
    expired = TenantFeatureFlag.objects.filter(enabled=True, expires_at__lt=now)
    count = expired.update(enabled=False)
    log.info("expire_feature_flags: disabled %d flags", count)
    return count


@shared_task(name="tenant.check_license_expiry")
def check_license_expiry_task():
    """Mark licenses inactive when they expire."""
    from platform.tenant.models import TenantLicense

    now = timezone.now()
    expired = TenantLicense.objects.filter(is_active=True, valid_until__lt=now)
    count = expired.update(is_active=False)
    log.info("check_license_expiry: deactivated %d licenses", count)
    return count


@shared_task(name="tenant.sync_realm_mapping")
def sync_realm_mapping_task(tenant_id: str):
    """Re-sync Keycloak realm info for a tenant (called after realm updates)."""
    from platform.tenant.models import Tenant

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        log.warning("sync_realm_mapping: tenant %s not found", tenant_id)
        return

    log.info("sync_realm_mapping: synced realm for tenant %s", tenant.slug)
    return tenant.keycloak_realm_name
