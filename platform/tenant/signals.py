"""
CyberCom Multi-Tenant Framework — Django Signal Handlers.
Emits audit events and Kafka outbox entries on tenant lifecycle changes.
"""
import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from platform.tenant.models import (
    Tenant, TenantFeatureFlag, TenantDomain,
    TenantLicense, TenantComplianceProfile,
)

log = logging.getLogger(__name__)


@receiver(pre_save, sender=Tenant)
def tenant_status_change_audit(sender, instance: Tenant, **kwargs):
    if not instance.pk:
        return
    try:
        previous = Tenant.objects.get(pk=instance.pk)
    except Tenant.DoesNotExist:
        return

    if previous.status == instance.status:
        return

    from platform.tenant.services import TenantEventEmitter, _metrics
    from platform.audit.models import AuditLog, AuditAction

    try:
        AuditLog.objects.create(
            action=AuditAction.UPDATE,
            resource_type="tenant",
            resource_id=str(instance.id),
            description=f"Tenant status changed {previous.status} -> {instance.status}",
            metadata={"from": previous.status, "to": instance.status, "slug": instance.slug},
        )
    except Exception:
        log.exception("Failed to write audit log for tenant status change")

    TenantEventEmitter.emit(
        f"tenant.{instance.status}",
        instance,
        {"from_status": previous.status, "to_status": instance.status},
    )


@receiver(post_save, sender=TenantFeatureFlag)
def feature_flag_audit(sender, instance: TenantFeatureFlag, created: bool, **kwargs):
    from platform.audit.models import AuditLog, AuditAction
    action = AuditAction.CREATE if created else AuditAction.UPDATE
    try:
        AuditLog.objects.create(
            action=action,
            resource_type="tenant_feature_flag",
            resource_id=str(instance.id),
            description=f"Feature flag '{instance.key}' set to {instance.enabled}",
            metadata={"tenant_slug": instance.tenant.slug, "key": instance.key, "enabled": instance.enabled},
        )
    except Exception:
        log.exception("Failed to write audit for feature flag change")


@receiver(post_save, sender=TenantDomain)
def domain_verification_audit(sender, instance: TenantDomain, created: bool, **kwargs):
    if not instance.is_verified:
        return
    from platform.audit.models import AuditLog, AuditAction
    try:
        AuditLog.objects.create(
            action=AuditAction.UPDATE,
            resource_type="tenant_domain",
            resource_id=str(instance.id),
            description=f"Domain {instance.domain} verified",
            metadata={"tenant_slug": instance.tenant.slug, "domain": instance.domain},
        )
    except Exception:
        log.exception("Failed to write audit for domain verification")


@receiver(post_save, sender=TenantLicense)
def license_change_audit(sender, instance: TenantLicense, created: bool, **kwargs):
    from platform.audit.models import AuditLog, AuditAction
    action = AuditAction.CREATE if created else AuditAction.UPDATE
    try:
        AuditLog.objects.create(
            action=action,
            resource_type="tenant_license",
            resource_id=str(instance.id),
            description=f"License {instance.module} ({instance.license_type}) {'granted' if created else 'updated'}",
            metadata={"tenant_slug": instance.tenant.slug, "module": instance.module, "is_active": instance.is_active},
        )
    except Exception:
        log.exception("Failed to write audit for license change")


@receiver(post_save, sender=TenantComplianceProfile)
def compliance_profile_audit(sender, instance: TenantComplianceProfile, created: bool, **kwargs):
    if not created:
        return
    from platform.audit.models import AuditLog, AuditAction
    try:
        AuditLog.objects.create(
            action=AuditAction.CREATE,
            resource_type="tenant_compliance_profile",
            resource_id=str(instance.id),
            description=f"Compliance framework {instance.framework} added",
            metadata={"tenant_slug": instance.tenant.slug, "framework": instance.framework},
        )
    except Exception:
        log.exception("Failed to write audit for compliance profile")
