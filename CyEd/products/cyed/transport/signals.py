"""RFID boarding events → automated guardian notification."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from products.cyed.transport.models import RfidBoardingEvent


@receiver(post_save, sender=RfidBoardingEvent, dispatch_uid="cyed_rfid_notify")
def _on_boarding_event(sender, instance, created, **kwargs):
    if not created:
        return
    from products.cyed.notifications.delivery import deliver
    from products.cyed.notifications.models import Notification

    student = instance.student
    verb = "safely boarded" if instance.event_type == "board" else "safely got off"
    bus = instance.bus.identifier if instance.bus else "the bus"
    when = instance.occurred_at.strftime("%I:%M %p") if instance.occurred_at else ""
    body = f"{student.first_name} {verb} {bus}" + (f" at {when}" if when else "") + "."

    for g in student.guardians.all():
        n = Notification.objects.create(
            tenant_id=instance.tenant_id,
            student=student,
            recipient_kind="guardian",
            recipient_name=f"{g.first_name} {g.last_name}".strip(),
            recipient_email=g.email,
            recipient_phone=g.phone,
            channel="in_app",
            category="attendance",
            subject=f"Bus {instance.event_type}: {student.first_name}",
            body=body,
            related_model="cyed_transport.RfidBoardingEvent",
            related_id=str(instance.id),
            status="queued",
        )
        deliver(n)
