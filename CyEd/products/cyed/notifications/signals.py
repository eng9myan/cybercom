"""Trigger guardian notifications when an absence is recorded."""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from products.cyed.attendance.models import AttendanceMark
from products.cyed.notifications.services import notify_guardians_of_absence


@receiver(post_save, sender=AttendanceMark, dispatch_uid="cyed_absence_notify")
def _on_attendance_mark(sender, instance, created, **kwargs):
    """
    Alert guardians about a single mark, once it is durably recorded.

    Deferred to `on_commit` rather than sent inline: a request that fails after
    this point would otherwise have already told a parent their child is absent
    when no such mark exists. In-app notifications roll back with the
    transaction and hide the flaw, but an SMS about a child's whereabouts
    cannot be recalled.

    Bulk roll marking does not pass through here — it uses `bulk_create`, which
    fires no signals, and dispatches its own notifications the same way. See
    `products/cyed/attendance/services.take_roll`.
    """
    if not created:
        return
    if instance.status not in {"absent", "late", "left_early"}:
        return

    mark_id = instance.id
    transaction.on_commit(lambda: _notify(mark_id))


def _notify(mark_id):
    mark = AttendanceMark.objects.select_related("student", "roll_call").filter(id=mark_id).first()
    if mark is not None:
        notify_guardians_of_absence(mark)
