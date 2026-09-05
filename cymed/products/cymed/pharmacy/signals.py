"""
CyMed Pharmacy Edition — Signal Handlers
Publishes canonical domain events (platform.canonical.events — M9 cutover,
was the legacy Program 2.5 OutboxEvent transactional outbox).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


def _publish_event(event_type: str, aggregate_type: str, aggregate_id, payload: dict, tenant_id=None):
    """Helper to publish a canonical domain event."""
    try:
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            payload=payload,
        )
    except Exception:
        pass  # Fail silently — events are best-effort


# Prescription events
@receiver(post_save, sender="cymed_pharmacy.Prescription")
def on_prescription_saved(sender, instance, created, **kwargs):
    if created:
        _publish_event(
            event_type="cymed.pharmacy.prescription.created",
            aggregate_type="Prescription",
            aggregate_id=instance.id,
            payload={
                "prescription_id": str(instance.id),
                "prescription_number": instance.prescription_number,
                "patient_id": str(instance.patient_id),
                "type": instance.prescription_type,
            },
            tenant_id=instance.tenant_id,
        )


# Dispense events
@receiver(post_save, sender="cymed_pharmacy.DispenseOrder")
def on_dispense_saved(sender, instance, created, **kwargs):
    if not created and instance.status == "completed":
        _publish_event(
            event_type="cymed.pharmacy.dispense.completed",
            aggregate_type="DispenseOrder",
            aggregate_id=instance.id,
            payload={
                "dispense_id": str(instance.id),
                "prescription_id": str(instance.prescription_id)
                if instance.prescription_id
                else None,
                "patient_id": str(instance.patient_id),
            },
            tenant_id=instance.tenant_id,
        )
