from django.db.models.signals import post_save
from django.dispatch import receiver


def _publish(tenant_id, event_type, payload):
    try:
        from platform.events.outbox import OutboxEvent

        OutboxEvent.publish(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


@receiver(post_save, sender="cymed_provider_workspace.ProviderWorkspace")
def on_workspace_created(sender, instance, created, **kwargs):
    if created:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.provider.workspace.created",
            payload={
                "workspace_id": str(instance.id),
                "provider_id": str(instance.provider_id),
                "provider_type": instance.provider_type,
            },
        )


@receiver(post_save, sender="cymed_provider_clinical_tasks.ClinicalTask")
def on_task_created(sender, instance, created, **kwargs):
    if created:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.provider.task.created",
            payload={
                "task_id": str(instance.id),
                "assigned_to": str(instance.assigned_to_provider_id),
                "priority": instance.priority,
                "task_type": instance.task_type,
            },
        )


@receiver(post_save, sender="cymed_provider_approvals.ApprovalRequest")
def on_approval_requested(sender, instance, created, **kwargs):
    if created:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.provider.approval.requested",
            payload={
                "approval_id": str(instance.id),
                "approval_type": instance.approval_type,
                "requested_by": str(instance.requested_by_provider_id),
                "approver_id": str(instance.approver_id),
            },
        )
