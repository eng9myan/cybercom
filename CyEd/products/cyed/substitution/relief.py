"""
Relief (CRT) booking.

The step after the substitution engine runs out of colleagues. Before this, an
uncovered class was a dead end: the plan said "uncovered" and the daily
organiser went back to a spreadsheet of phone numbers.

The rules that matter are the ones that stop a class being left unattended
while the board says otherwise:

* A CRT without current clearances is never offered work. Same rule as employed
  staff — a casual stands in front of the same children.
* An offer is not cover. A booking counts toward covering a class only once the
  CRT has accepted; anything else puts an uncovered class on the board as done.
* One live booking per person per day, enforced by the database, because the
  failure mode is a CRT accepting two schools' work and one class standing in a
  corridor.
"""

from django.db import transaction
from django.utils import timezone

from products.cyed.substitution.models import (
    ReliefAvailability,
    ReliefBooking,
    ReliefTeacher,
)


class ReliefError(Exception):
    """A relief action was refused for a business reason (→ HTTP 400/409)."""


def _as_date(value):
    """
    Coerce a day to a `date`.

    Dates arrive from query strings and request bodies as text, and the
    clearance checks compare them against real dates. Parsing here rather than
    in each caller means an ISO string and a `date` behave identically — the
    alternative raised a TypeError deep inside an expiry comparison.
    """
    from datetime import date as _date, datetime

    if isinstance(value, _date):
        return value
    if not value:
        return timezone.localdate()
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        raise ReliefError(f"'{value}' is not a date (expected YYYY-MM-DD).")


def available_on(tenant_id, day, *, subject="", campus_id=None):
    """
    CRTs who can work `day`, ordered so the most suitable is offered first.

    Availability must be stated, not assumed: a CRT who has not said they are
    free that day is not called. Ringing people at 7am on the off-chance is
    what this replaces.
    """
    day = _as_date(day)
    stated = ReliefAvailability.objects.filter(tenant_id=tenant_id, date=day).values_list(
        "relief_teacher_id", flat=True
    )
    booked = ReliefBooking.objects.filter(
        tenant_id=tenant_id, date=day, status__in=["offered", "accepted"]
    ).values_list("relief_teacher_id", flat=True)

    teachers = ReliefTeacher.objects.filter(
        tenant_id=tenant_id, status="active", id__in=list(stated)
    ).exclude(id__in=list(booked))
    if campus_id:
        teachers = teachers.filter(campus_id=campus_id)

    rows = []
    for teacher in teachers:
        state = teacher.clearance_state(day)
        if not state["may_teach"]:
            # Excluded rather than shown-and-greyed: an organiser under time
            # pressure will ring the first name on the list.
            continue
        rows.append({
            "relief_teacher": str(teacher.id),
            "name": teacher.full_name(),
            "phone": teacher.phone,
            "email": teacher.email,
            "agency": teacher.agency,
            "subjects": teacher.subjects,
            "daily_rate": str(teacher.daily_rate),
            "subject_match": _matches_subject(teacher.subjects, subject),
        })

    # Subject specialists first, then by rate — a school covering Year 11
    # Chemistry cares more about the match than the price.
    rows.sort(key=lambda r: (not r["subject_match"], float(r["daily_rate"] or 0), r["name"]))
    return rows


# Shortest prefix two subject names must share to count as the same subject.
# Four characters matches "Maths"/"Mathematics" and "Sci"/"Science" while
# keeping "History" and "Hospitality" apart.
_SUBJECT_PREFIX = 4


def _matches_subject(listed: str, wanted: str) -> bool:
    """
    Loose match on purpose: a school asking for "Maths" should find someone
    listed as "Mathematics".

    Substring alone does not do that — "mathematics" does not contain "maths" —
    so a shared prefix is checked too. Teachers type subject names freehand and
    an exact-match search returns nobody at 7:30am, which sends the organiser
    back to the spreadsheet this replaces.
    """
    if not wanted or not listed:
        return False
    wanted = wanted.strip().lower()
    for part in listed.lower().split(","):
        part = part.strip()
        if not part:
            continue
        if wanted in part or part in wanted:
            return True
        shared = 0
        for a, b in zip(wanted, part):
            if a != b:
                break
            shared += 1
        if shared >= _SUBJECT_PREFIX:
            return True
    return False


def unclearable(tenant_id, day=None):
    """
    Active CRTs who cannot be booked because their clearances are missing or
    expired — the register's chase list, and the reason a search came up empty.
    """
    day = _as_date(day)
    rows = []
    for teacher in ReliefTeacher.objects.filter(tenant_id=tenant_id, status="active"):
        state = teacher.clearance_state(day)
        if state["may_teach"]:
            continue
        rows.append({
            "relief_teacher": str(teacher.id),
            "name": teacher.full_name(),
            "agency": teacher.agency,
            "problems": state["problems"],
            "wwcc_expires_on": (
                teacher.wwcc_expires_on.isoformat() if teacher.wwcc_expires_on else None
            ),
        })
    return rows


@transaction.atomic
def offer(teacher, *, day, plan=None, covering_for=None, periods="", is_full_day=True,
          offered_by="", cost_centre=""):
    """
    Offer a day's work. Refuses anything that would put an unbookable person in
    front of a class.
    """
    day = _as_date(day)
    if teacher.status == "do_not_book":
        reason = teacher.do_not_book_reason or "marked do-not-book"
        raise ReliefError(f"{teacher.full_name()} is not to be booked: {reason}.")
    if teacher.status != "active":
        raise ReliefError(f"{teacher.full_name()} is not active on the relief register.")

    state = teacher.clearance_state(day)
    if not state["may_teach"]:
        raise ReliefError(
            f"{teacher.full_name()} cannot be booked: {', '.join(state['problems'])}."
        )

    if ReliefBooking.objects.filter(
        tenant_id=teacher.tenant_id, relief_teacher=teacher, date=day,
        status__in=["offered", "accepted"],
    ).exists():
        raise ReliefError(f"{teacher.full_name()} already has a booking on {day}.")

    return ReliefBooking.objects.create(
        tenant_id=teacher.tenant_id,
        relief_teacher=teacher,
        date=day,
        plan=plan,
        covering_for=covering_for,
        periods=periods[:255],
        is_full_day=is_full_day,
        status="offered",
        offered_by=offered_by[:255],
        # Frozen now: a rate rise next term must not rewrite what was agreed.
        agreed_rate=teacher.daily_rate if is_full_day else teacher.half_day_rate,
        cost_centre=cost_centre[:100],
    )


def respond(booking, *, accepted: bool, note=""):
    """The CRT's answer. Only a live offer can be answered."""
    if booking.status != "offered":
        raise ReliefError(f"This booking is already {booking.status}.")
    booking.status = "accepted" if accepted else "declined"
    booking.responded_at = timezone.now()
    booking.response_note = note[:255]
    booking.save(update_fields=["status", "responded_at", "response_note", "updated_at"])
    return booking


def cancel(booking, *, reason=""):
    """
    School cancels. Kept as a row rather than deleted — a CRT who turned down
    other work deserves a record of it, and some agreements pay a cancellation
    fee.
    """
    if booking.status in ("cancelled", "completed"):
        raise ReliefError(f"This booking is already {booking.status}.")
    booking.status = "cancelled"
    booking.response_note = (reason or booking.response_note)[:255]
    booking.save(update_fields=["status", "response_note", "updated_at"])
    return booking


def cover_for_plan(plan):
    """
    Which of a plan's gaps are now covered by an accepted relief booking.

    Only accepted bookings count. An offer nobody has answered is not cover,
    and showing it as such is how a class ends up unattended with a board that
    says otherwise.
    """
    bookings = ReliefBooking.objects.filter(
        tenant_id=plan.tenant_id, plan=plan, status="accepted"
    ).select_related("relief_teacher")
    return [
        {
            "booking": str(b.id),
            "relief_teacher": b.relief_teacher.full_name(),
            "phone": b.relief_teacher.phone,
            "periods": b.periods,
            "is_full_day": b.is_full_day,
            "agreed_rate": str(b.agreed_rate),
        }
        for b in bookings
    ]


def cost_report(tenant_id, *, date_from=None, date_to=None):
    """
    What relief has cost. The number a business manager is asked for at every
    finance meeting and previously had to assemble by hand.
    """
    from decimal import Decimal

    bookings = ReliefBooking.objects.filter(
        tenant_id=tenant_id, status__in=["accepted", "completed"]
    ).select_related("relief_teacher")
    if date_from:
        bookings = bookings.filter(date__gte=date_from)
    if date_to:
        bookings = bookings.filter(date__lte=date_to)

    by_teacher, total = {}, Decimal("0")
    for booking in bookings:
        total += Decimal(booking.agreed_rate)
        row = by_teacher.setdefault(
            str(booking.relief_teacher_id),
            {
                "relief_teacher": str(booking.relief_teacher_id),
                "name": booking.relief_teacher.full_name(),
                "agency": booking.relief_teacher.agency,
                "days": 0,
                "cost": Decimal("0"),
            },
        )
        row["days"] += 1
        row["cost"] += Decimal(booking.agreed_rate)

    rows = sorted(by_teacher.values(), key=lambda r: r["cost"], reverse=True)
    for row in rows:
        row["cost"] = str(row["cost"])
    return {"total_cost": str(total), "bookings": bookings.count(), "by_teacher": rows}
