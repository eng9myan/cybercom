"""
Excursions: consent, payment and readiness as one thing.

Consent lived in `docsign`, charges lived in `fees`, and participation was a
row with a `consent_given` boolean beside them. Nothing joined the three, so
the question a teacher asks at 8:40am on the morning of a trip — *who is
allowed on the bus* — could not be answered without cross-checking three
screens and a paper pile.

The rules encoded here are the ones that make that answer trustworthy:

* A child is cleared when they are confirmed, their permission is signed, and
  the money is settled *or* explicitly waived. A waiver is a decision the
  school records, not an absence of data.
* Issuing an excursion raises the consent form and the charge together, so a
  family gets one job rather than two arriving days apart.
* The roll travels with the medical plans. A supervising teacher off site with
  no signal needs what to do about a child's anaphylaxis, not a link to it.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from products.cyed.events.models import Event, EventParticipation


class ExcursionError(Exception):
    """An excursion action was refused for a business reason (→ HTTP 400/409)."""


@transaction.atomic
def invite(event, *, student_ids, issued_by=""):
    """
    Add students, raising the consent form and the charge for each.

    Both at once and idempotently: re-running after a late enrolment tops up
    the party rather than duplicating documents and invoices for everyone
    already on it.
    """
    if event.max_participants:
        already = event.participations.exclude(status="declined").count()
        room = event.max_participants - already
        if len(student_ids) > room:
            raise ExcursionError(
                f"Only {max(0, room)} place(s) left on this excursion "
                f"({event.max_participants} maximum)."
            )

    existing = set(
        str(s) for s in event.participations.values_list("student_id", flat=True)
    )
    created = []
    for student_id in student_ids:
        if str(student_id) in existing:
            continue
        participation = EventParticipation.objects.create(
            tenant_id=event.tenant_id, event=event, student_id=student_id, status="invited"
        )
        if event.requires_consent:
            participation.consent_document = _raise_consent(event, participation, issued_by)
        if event.charge_students and event.cost > 0:
            participation.invoice = _raise_charge(event, participation)
        participation.save(update_fields=["consent_document", "invoice", "updated_at"])
        created.append(participation)
    return created


def _raise_consent(event, participation, issued_by):
    """Create the permission form the family signs."""
    from products.cyed.docsign.models import SignableDocument

    student = participation.student
    body = (
        f"Permission for {student.first_name} {student.last_name} to attend "
        f"{event.name}.\n\n"
        f"When: {event.start_at:%d %B %Y} — {event.location or 'see details'}\n"
        f"{'Departs: ' + event.departs_at.strftime('%H:%M') if event.departs_at else ''}"
        f"{' · Returns: ' + event.returns_at.strftime('%H:%M') if event.returns_at else ''}\n"
        f"{event.transport_details}\n\n"
        f"{event.description}\n\n"
        f"What to bring: {event.what_to_bring or 'Nothing in particular.'}"
    )
    return SignableDocument.objects.create(
        tenant_id=event.tenant_id,
        title=f"Permission: {event.name} — {student.first_name} {student.last_name}",
        doc_type="permission_slip",
        body=body,
        student=student,
        created_by=issued_by[:255],
        due_date=event.permission_deadline,
    )


def _raise_charge(event, participation):
    """Raise the excursion fee as an ordinary invoice, on the family's account."""
    from products.cyed.fees.models import Invoice

    return Invoice.objects.create(
        tenant_id=event.tenant_id,
        student=participation.student,
        description=f"{event.name} — excursion",
        amount=Decimal(event.cost),
        due_date=event.permission_deadline or (
            event.start_at.date() if event.start_at else None
        ),
        status="issued",
        issued_on=timezone.localdate(),
    )


def waive_fee(participation, *, reason, actor=""):
    """
    A child whose family cannot pay still goes.

    Recorded as a decision rather than left as an unpaid invoice, so the
    readiness list can tell "the school decided this" apart from "nobody has
    chased this family".
    """
    if not (reason or "").strip():
        raise ExcursionError("Record why the fee is being waived.")
    if participation.fee_waived:
        raise ExcursionError("This fee has already been waived.")

    participation.fee_waived = True
    participation.waiver_reason = reason.strip()[:255]
    participation.save(update_fields=["fee_waived", "waiver_reason", "updated_at"])

    if participation.invoice_id:
        # Cancel rather than delete: the ledger should show that a charge was
        # raised and then written off, not that it never existed.
        invoice = participation.invoice
        invoice.status = "cancelled"
        invoice.save(update_fields=["status", "updated_at"])

    Event.objects.filter(pk=participation.event_id).update(
        hardship_waivers=participation.event.hardship_waivers + 1
    )
    return participation


def confirm(participation, *, responded_by="", emergency_contact=""):
    """
    A family says yes. Does not clear the child on its own — the permission
    still has to be signed and the fee settled.
    """
    if participation.status == "confirmed":
        return participation
    participation.status = "confirmed"
    participation.responded_by = responded_by[:255]
    participation.emergency_contact = emergency_contact[:255]
    participation.save(update_fields=[
        "status", "responded_by", "emergency_contact", "updated_at",
    ])
    return participation


def readiness(event) -> dict:
    """
    Who is cleared, and precisely what is missing for everyone else.

    "Not ready" on its own sends an office worker back through three systems.
    Each row says which of consent, payment or confirmation is outstanding, so
    the chase list writes itself.
    """
    rows = []
    participations = event.participations.select_related(
        "student", "consent_document", "invoice"
    ).exclude(status="declined")

    for participation in participations:
        missing = []
        if participation.status != "confirmed":
            missing.append("not confirmed")
        if not participation.is_consented():
            missing.append("permission not signed")
        if not participation.is_paid():
            missing.append("fee unpaid")

        student = participation.student
        rows.append({
            "participation": str(participation.id),
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "status": participation.status,
            "consented": participation.is_consented(),
            "paid": participation.is_paid(),
            "fee_waived": participation.fee_waived,
            "cleared": participation.is_cleared(),
            "missing": missing,
        })

    rows.sort(key=lambda r: (r["cleared"], r["name"]))
    cleared = sum(1 for r in rows if r["cleared"])
    return {
        "event": str(event.id),
        "name": event.name,
        "starts": event.start_at,
        "permission_deadline": (
            event.permission_deadline.isoformat() if event.permission_deadline else None
        ),
        "invited": len(rows),
        "cleared": cleared,
        "not_ready": len(rows) - cleared,
        "results": rows,
    }


def excursion_roll(event) -> dict:
    """
    The roll a supervising teacher takes off site.

    Carries the medical plans in full rather than a link: a teacher in a car
    park with no signal needs to know what to do about a child's anaphylaxis,
    not where to read about it.
    """
    from products.cyed.health.services import critical_plans

    cleared = [
        p for p in event.participations.select_related("student", "invoice", "consent_document")
        if p.is_cleared()
    ]
    student_ids = [p.student_id for p in cleared]
    plans = {p["student"]: p for p in critical_plans(event.tenant_id, student_ids=student_ids)}

    rows = []
    for participation in cleared:
        student = participation.student
        row = {
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "emergency_contact": participation.emergency_contact,
        }
        plan = plans.get(str(student.id))
        if plan:
            row["medical"] = {
                "condition": plan["plan_type_display"],
                "severity": plan["severity"],
                "triggers": plan["triggers"],
                "steps": plan["emergency_steps"],
                "medication": plan["medication"],
                "medication_location": plan["medication_location"],
            }
        rows.append(row)

    # Students with a medical plan first: the supervising teacher should read
    # those before the bus leaves, not discover them at the destination.
    rows.sort(key=lambda r: ("medical" not in r, r["name"]))
    return {
        "event": str(event.id),
        "name": event.name,
        "staff_in_charge": (
            f"{event.staff_in_charge.first_name} {event.staff_in_charge.last_name}".strip()
            if event.staff_in_charge_id else ""
        ),
        "count": len(rows),
        "with_medical_plans": sum(1 for r in rows if "medical" in r),
        "students": rows,
    }


def chase_list(event):
    """
    Families to contact about an unreturned permission, past the deadline.

    Deliberately only past the deadline: chasing a family a fortnight early is
    how a school teaches parents to ignore its messages.
    """
    if event.permission_deadline and timezone.localdate() < event.permission_deadline:
        return {"due": False, "deadline": event.permission_deadline.isoformat(), "results": []}

    rows = [r for r in readiness(event)["results"] if not r["cleared"]]
    return {
        "due": True,
        "deadline": (
            event.permission_deadline.isoformat() if event.permission_deadline else None
        ),
        "count": len(rows),
        "results": rows,
    }
