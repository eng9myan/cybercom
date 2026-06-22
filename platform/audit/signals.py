"""
Audit & Compliance signals. Auto-record high-value model changes.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import (
    AuditAction, AuditLog,
    ComplianceViolation, LegalHold, LegalHoldStatus, ViolationStatus,
)

log = logging.getLogger(__name__)


@receiver(pre_save, sender=LegalHold)
def legal_hold_status_audit(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        previous = LegalHold.objects.get(pk=instance.pk)
        if previous.status != instance.status:
            AuditLog.objects.create(
                tenant_id=instance.tenant_id,
                action=AuditAction.UPDATE,
                resource_type="legal_hold",
                resource_id=str(instance.id),
                description=f"Legal hold status: {previous.status} -> {instance.status}",
                metadata={"from": previous.status, "to": instance.status, "name": instance.name},
            )
    except Exception:
        log.exception("Failed to audit legal_hold status change")


@receiver(post_save, sender=ComplianceViolation)
def violation_status_audit(sender, instance, created, **kwargs):
    try:
        if created:
            AuditLog.objects.create(
                tenant_id=instance.tenant_id,
                action=AuditAction.CREATE,
                resource_type="compliance_violation",
                resource_id=str(instance.id),
                description=f"Violation recorded: {instance.rule.rule_id} ({instance.rule.severity})",
                metadata={"rule_id": instance.rule.rule_id, "severity": instance.rule.severity},
            )
        elif instance.status == ViolationStatus.REMEDIATED:
            AuditLog.objects.create(
                tenant_id=instance.tenant_id,
                action=AuditAction.UPDATE,
                resource_type="compliance_violation",
                resource_id=str(instance.id),
                description=f"Violation remediated: {instance.rule.rule_id}",
                metadata={"remediated_by": instance.remediated_by},
            )
    except Exception:
        log.exception("Failed to audit compliance violation")
