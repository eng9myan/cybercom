"""
CyMed Pharmacy Edition — Signal Handlers
Publishes domain events via Program 2.5 Event Framework (OutboxEvent).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


def _publish_event(topic: str, event_type: str, payload: dict, tenant_id=None):
    """Helper to publish via OutboxEvent (Program 2.5)."""
    try:
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic=topic,
            event_type=event_type,
            payload=payload,
        )
    except Exception:
        pass  # Fail silently — events are best-effort


# Prescription events
@receiver(post_save, sender="cymed_pharmacy.Prescription")
def on_prescription_saved(sender, instance, created, **kwargs):
    if created:
        _publish_event(
            topic="cymed.pharmacy.prescription.created",
            event_type="cymed.pharmacy.prescription.created",
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
            topic="cymed.pharmacy.dispense.completed",
            event_type="cymed.pharmacy.dispense.completed",
            payload={
                "dispense_id": str(instance.id),
                "prescription_id": str(instance.prescription_id)
                if instance.prescription_id
                else None,
                "patient_id": str(instance.patient_id),
            },
            tenant_id=instance.tenant_id,
        )
