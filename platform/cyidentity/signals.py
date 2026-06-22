"""
CyIdentity Django signals — lifecycle hooks for audit + metrics emission.
"""
from __future__ import annotations

import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from platform.cyidentity.models import (
    BreakGlassAccess,
    BreakGlassStatus,
    ClientSecret,
    IdentityRealm,
    LoginAudit,
    RealmStatus,
    UserSession,
)
from platform.cyidentity.services import AuditService, IdentityEventEmitter, metrics

logger = logging.getLogger("cybercom.cyidentity.signals")


@receiver(pre_save, sender=IdentityRealm)
def realm_status_change_audit(sender, instance: IdentityRealm, **kwargs):
    """Emit audit row when realm transitions status."""
    if not instance.pk:
        return
    try:
        prior = IdentityRealm.objects.get(pk=instance.pk)
    except IdentityRealm.DoesNotExist:
        return
    if prior.status != instance.status:
        AuditService.record(
            action="update",
            resource_type="realm",
            resource_id=str(instance.id),
            tenant_id=instance.tenant_id,
            status="success",
            details={"event": "status_change", "from": prior.status, "to": instance.status},
        )
        IdentityEventEmitter.emit(
            "cyidentity.realm.status_changed",
            {"realm_id": str(instance.id), "realm_name": instance.realm_name, "from": prior.status, "to": instance.status},
        )
        if instance.status == RealmStatus.DECOMMISSIONED:
            metrics.realm_decommissioned_total += 1


@receiver(post_save, sender=ClientSecret)
def client_secret_created_audit(sender, instance: ClientSecret, created, **kwargs):
    if created:
        AuditService.record(
            action="create",
            resource_type="client_secret",
            resource_id=str(instance.id),
            tenant_id=instance.tenant_id,
            user_id=instance.created_by,
            status="success",
            details={"client_id": instance.client.client_id, "event": "secret_created"},
        )


@receiver(post_delete, sender=ClientSecret)
def client_secret_revoked_audit(sender, instance: ClientSecret, **kwargs):
    AuditService.record(
        action="delete",
        resource_type="client_secret",
        resource_id=str(instance.id),
        tenant_id=instance.tenant_id,
        status="success",
        details={"client_id": instance.client.client_id, "event": "secret_revoked"},
    )


@receiver(post_save, sender=UserSession)
def session_status_audit(sender, instance: UserSession, created, **kwargs):
    if created:
        return
    AuditService.record(
        action="create" if instance.status == "active" else "update",
        resource_type="session",
        resource_id=str(instance.id),
        tenant_id=instance.tenant_id,
        user_id=str(instance.user_id),
        status="success",
        details={"event": "session_status", "status": instance.status},
    )


@receiver(post_save, sender=BreakGlassAccess)
def break_glass_audit(sender, instance: BreakGlassAccess, created, **kwargs):
    AuditService.record(
        action="break_glass",
        resource_type=instance.target_resource,
        resource_id=str(instance.id),
        tenant_id=instance.tenant_id,
        user_id=str(instance.user.keycloak_user_id) if instance.user_id else "",
        status="success",
        details={"event": "status", "status": instance.status, "reason": instance.reason},
    )


@receiver(post_save, sender=LoginAudit)
def login_audit_metric(sender, instance: LoginAudit, created, **kwargs):
    if not created:
        return
    if instance.outcome == "success":
        metrics.login_total += 1
    else:
        metrics.login_failure_total += 1
    if instance.outcome == "mfa_challenge":
        metrics.mfa_challenge_total += 1
    if instance.outcome == "mfa_failure":
        metrics.mfa_failure_total += 1
