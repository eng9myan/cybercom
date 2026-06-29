from django.db.models.signals import post_save
from django.dispatch import receiver


def _publish(tenant_id, event_type, payload):
    try:
        from platform.events.outbox import OutboxEvent

        OutboxEvent.publish(tenant_id=tenant_id, event_type=event_type, payload=payload)
    except Exception:
        pass


def _push_to_cygov(tenant_id, event_type, payload):
    """Push public health events to CyGov via CyIntegrationHub."""
    try:
        from platform.integrations.hub import CyIntegrationHub

        CyIntegrationHub.send(
            tenant_id=tenant_id,
            destination="cygov_health",
            event_type=event_type,
            payload=payload,
        )
    except Exception:
        pass


@receiver(post_save, sender="cymed_ph_surveillance.Outbreak")
def on_outbreak_created(sender, instance, created, **kwargs):
    if created:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.ph.outbreak.detected",
            payload={
                "outbreak_id": str(instance.id),
                "disease_code": instance.disease_code,
                "severity_level": instance.severity_level,
            },
        )
        _push_to_cygov(
            tenant_id=instance.tenant_id,
            event_type="cymed.ph.outbreak.detected",
            payload={"outbreak_id": str(instance.id), "disease_code": instance.disease_code},
        )


@receiver(post_save, sender="cymed_ph_surveillance.OutbreakAlert")
def on_outbreak_alert(sender, instance, created, **kwargs):
    if created and instance.alert_level in ("orange", "red"):
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.ph.outbreak.alert",
            payload={"alert_id": str(instance.id), "alert_level": instance.alert_level},
        )


@receiver(post_save, sender="cymed_ph_national_programs.ProgramEnrollment")
def on_program_enrollment(sender, instance, created, **kwargs):
    if created:
        _publish(
            tenant_id=instance.tenant_id,
            event_type="cymed.ph.program.enrollment",
            payload={"enrollment_id": str(instance.id), "program_id": str(instance.program_id)},
        )
