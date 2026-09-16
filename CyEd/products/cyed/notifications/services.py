"""Notification services: absence alerts and staff announcements."""

from products.cyed.notifications.delivery import deliver
from products.cyed.notifications.models import Notification

ABSENCE_STATUSES = {"absent", "late", "left_early"}


def _status_word(status):
    return {"absent": "absent", "late": "late", "left_early": "leaving early"}.get(status, status)


def notify_guardians_of_absence(mark):
    """
    Create + deliver an in-app notification to each guardian of the student for
    an absence/late/left-early mark. Duty-of-care; not gated on AI consent.
    Returns the created notifications (may be empty if no guardians).
    """
    if mark.status not in ABSENCE_STATUSES:
        return []
    student = mark.student
    created = []
    date = getattr(mark.roll_call, "date", None)
    for g in student.guardians.all():
        n = Notification.objects.create(
            tenant_id=mark.tenant_id,
            student=student,
            recipient_kind="guardian",
            recipient_name=f"{g.first_name} {g.last_name}".strip(),
            recipient_email=g.email,
            recipient_phone=g.phone,
            channel="in_app",
            category="attendance",
            subject=f"Attendance alert: {student.first_name} {student.last_name}",
            body=(
                f"{student.first_name} was marked {_status_word(mark.status)}"
                + (f" on {date}" if date else "")
                + ". Please contact the school if this is unexpected."
            ),
            related_model="cyed_attendance.AttendanceMark",
            related_id=str(mark.id),
            status="queued",
        )
        deliver(n)
        created.append(n)
    return created


def send_announcement(tenant_id, *, subject, body, student=None, category="announcement", channel="in_app"):
    """Send an announcement to a student's guardians, or all guardians in the tenant."""
    from products.cyed.sis.models import Guardian

    if student is not None:
        guardians = student.guardians.all()
    else:
        guardians = Guardian.objects.filter(tenant_id=tenant_id)

    created = []
    for g in guardians:
        n = Notification.objects.create(
            tenant_id=tenant_id,
            student=student,
            recipient_kind="guardian",
            recipient_name=f"{g.first_name} {g.last_name}".strip(),
            recipient_email=g.email,
            recipient_phone=g.phone,
            channel=channel,
            category=category,
            subject=subject,
            body=body,
            status="queued",
        )
        deliver(n)
        created.append(n)
    return created
