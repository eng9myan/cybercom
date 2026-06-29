"""
CyMed Patient Portal — Signal Handlers
Publishes domain events via Program 2.5 Event Framework (OutboxEvent).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


def _publish_event(topic: str, event_type: str, payload: dict, tenant_id=None):
    try:
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic=topic,
            event_type=event_type,
            payload=payload,
        )
    except Exception:
        pass


@receiver(post_save, sender="cymed_portal_accounts.PatientPortalAccount")
def on_account_created(sender, instance, created, **kwargs):
    if created:
        _publish_event(
            topic="cymed.portal.account.registered",
            event_type="cymed.portal.account.registered",
            payload={
                "account_id": str(instance.id),
                "patient_id": str(instance.patient_id),
            },
            tenant_id=instance.tenant_id,
        )


@receiver(post_save, sender="cymed_portal_appointments.PortalAppointmentRequest")
def on_appointment_requested(sender, instance, created, **kwargs):
    if created:
        _publish_event(
            topic="cymed.portal.appointment.requested",
            event_type="cymed.portal.appointment.requested",
            payload={
                "request_id": str(instance.id),
                "patient_id": str(instance.patient_id),
                "provider_id": str(instance.provider_id) if instance.provider_id else None,
            },
            tenant_id=instance.tenant_id,
        )
