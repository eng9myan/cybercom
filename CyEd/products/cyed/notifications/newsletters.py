"""
Newsletters: one composition, many recipients.

A newsletter is not a new kind of message — it fans out into ordinary
`Notification` rows and travels the same delivery path as an absence alert.
That is deliberate: it inherits the same honesty about what was actually sent,
the same retry, and the same per-recipient failure record. A parallel bulk
sender would have needed all of that rebuilt, and would have drifted.

Two rules worth stating:

**Sending is explicit and once.** A newsletter that goes out when it is saved
is one a school sends by accident, to everybody. `status` guards re-sends —
the second click must not mail the school twice.

**SMS is not offered for bulk.** A weekly newsletter to 900 families over SMS
is a bill nobody approved and, for most of them, a nuisance. Urgent SMS is what
the alert paths are for.
"""

from django.db import transaction
from django.utils import timezone


class NewsletterError(Exception):
    """A newsletter action was refused for a business reason (→ HTTP 400/409)."""


# Bulk sends are limited to channels a school can afford to send at scale.
BULK_CHANNELS = {"in_app", "email", "push"}


def audience_for(newsletter):
    """
    Who receives this newsletter.

    Guardians are resolved through their children so year-level targeting
    works: "Year 12 formal" should reach Year 12 families, and a guardian has
    no year level of their own.
    """
    from products.cyed.hr.models import Staff
    from products.cyed.sis.models import Guardian, Student

    tenant_id = newsletter.tenant_id
    years = {y.strip() for y in newsletter.year_levels.split(",") if y.strip()}

    recipients = []

    if newsletter.audience in ("parents", "all"):
        students = Student.objects.filter(tenant_id=tenant_id, enrolment_status="enrolled")
        if years:
            students = students.filter(year_level__in=[int(y) for y in years])
        if newsletter.campus_id:
            students = students.filter(campus_id=newsletter.campus_id)

        seen = set()
        for guardian in Guardian.objects.filter(
            tenant_id=tenant_id, students__in=students
        ).distinct():
            key = (guardian.email or "").lower()
            # A guardian with children in two year levels gets one copy, not
            # two — the commonest complaint about school bulk mail.
            if not key or key in seen:
                continue
            seen.add(key)
            recipients.append({
                "kind": "guardian",
                "name": f"{guardian.first_name} {guardian.last_name}".strip(),
                "email": guardian.email,
                "phone": guardian.phone,
            })

    if newsletter.audience in ("students", "all"):
        students = Student.objects.filter(tenant_id=tenant_id, enrolment_status="enrolled")
        if years:
            students = students.filter(year_level__in=[int(y) for y in years])
        if newsletter.campus_id:
            students = students.filter(campus_id=newsletter.campus_id)
        for student in students.exclude(email=""):
            recipients.append({
                "kind": "student",
                "name": f"{student.first_name} {student.last_name}".strip(),
                "email": student.email,
                "phone": "",
                "student": student,
            })

    if newsletter.audience in ("staff", "all"):
        staff = Staff.objects.filter(tenant_id=tenant_id, is_active=True).exclude(email="")
        if newsletter.campus_id:
            staff = staff.filter(campus_id=newsletter.campus_id)
        for person in staff:
            recipients.append({
                "kind": "staff",
                "name": f"{person.first_name} {person.last_name}".strip(),
                "email": person.email,
                "phone": person.phone,
            })

    return recipients


def preview(newsletter):
    """
    How many people this would reach, before anybody presses send.

    Worth having: "all parents" and "Year 9 parents" look identical on a form
    and differ by nine hundred recipients.
    """
    recipients = audience_for(newsletter)
    counts = {}
    for recipient in recipients:
        counts[recipient["kind"]] = counts.get(recipient["kind"], 0) + 1
    return {"total": len(recipients), "by_kind": counts}


@transaction.atomic
def send(newsletter, *, sent_by=""):
    """
    Fan the newsletter out into notifications and deliver them.

    Guarded against a second click: a school that mails every family twice
    spends the next hour apologising.
    """
    from products.cyed.notifications.delivery import deliver
    from products.cyed.notifications.models import Notification

    if newsletter.status == "sent":
        raise NewsletterError(
            f"This newsletter was already sent on {newsletter.sent_at:%d %b %Y at %H:%M} "
            f"to {newsletter.recipients} recipient(s)."
        )
    if newsletter.status == "sending":
        raise NewsletterError("This newsletter is already being sent.")
    if newsletter.channel not in BULK_CHANNELS:
        raise NewsletterError(
            f"'{newsletter.channel}' cannot be used for a bulk send. "
            f"Available: {', '.join(sorted(BULK_CHANNELS))}."
        )

    recipients = audience_for(newsletter)
    if not recipients:
        raise NewsletterError(
            "That audience matches nobody. Check the year levels and campus."
        )

    newsletter.status = "sending"
    newsletter.save(update_fields=["status", "updated_at"])

    sent = 0
    for recipient in recipients:
        note = Notification.objects.create(
            tenant_id=newsletter.tenant_id,
            student=recipient.get("student"),
            recipient_kind=recipient["kind"],
            recipient_name=recipient["name"],
            recipient_email=recipient["email"],
            recipient_phone=recipient["phone"],
            channel=newsletter.channel,
            category="announcement",
            subject=newsletter.title,
            body=newsletter.body,
            related_model="cyed_notifications.Newsletter",
            related_id=str(newsletter.id),
            status="queued",
        )
        deliver(note)
        sent += 1

    newsletter.status = "sent"
    newsletter.sent_at = timezone.now()
    newsletter.sent_by = sent_by[:255]
    newsletter.recipients = sent
    newsletter.save(update_fields=[
        "status", "sent_at", "sent_by", "recipients", "updated_at",
    ])
    return newsletter


def delivery_report(newsletter):
    """
    What actually happened to a sent newsletter.

    Counts come from the notification rows rather than the send loop, so a
    message that failed at the provider is reported as failed here — the whole
    reason for reusing the ordinary delivery path.
    """
    from products.cyed.notifications.models import Notification

    rows = Notification.objects.filter(
        tenant_id=newsletter.tenant_id,
        related_model="cyed_notifications.Newsletter",
        related_id=str(newsletter.id),
    )
    counts = {}
    for status in rows.values_list("status", flat=True):
        counts[status] = counts.get(status, 0) + 1
    return {
        "newsletter": str(newsletter.id),
        "title": newsletter.title,
        "sent_at": newsletter.sent_at,
        "recipients": newsletter.recipients,
        "by_status": counts,
        "failures": [
            {"recipient": r.recipient_name, "error": r.error}
            for r in rows.filter(status="failed")[:50]
        ],
    }
