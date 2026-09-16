"""
Parent–teacher interview booking.

The rules here are all about fairness and about not promising a family an
appointment that does not exist:

* A slot holds one booking, enforced at the database. Two parents pressing
  "book" the instant a round opens is the normal case, not an edge case.
* A family may only book for their own child, and only within the round's
  window.
* A per-student cap stops one organised family taking every slot with a popular
  teacher before other families have opened the page — the commonest complaint
  about these systems.
* Cancelling frees the slot and keeps the row: "booked then cancelled" reads
  very differently to a teacher than "never booked".
"""

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from products.cyed.meetings.models import InterviewBooking, InterviewRound, InterviewSlot


class InterviewError(Exception):
    """A booking action was refused for a business reason (→ HTTP 400/409)."""


def generate_slots(round_obj, *, teacher, start, end, duration_minutes=10,
                   break_after=None, break_minutes=0, location=""):
    """
    Lay out a teacher's evening in fixed windows.

    Teachers set up an evening as "5pm to 8pm, ten minutes each", not by
    entering eighteen individual times. `break_after` inserts a breather every
    N slots — an evening of back-to-back interviews with no gap is how a
    schedule ends up running twenty minutes late by 7pm.
    """
    if end <= start:
        raise InterviewError("The finish time must be after the start time.")
    if duration_minutes <= 0:
        raise InterviewError("Slots need a positive duration.")

    created, cursor, since_break = [], start, 0
    while cursor + timedelta(minutes=duration_minutes) <= end:
        created.append(InterviewSlot(
            tenant_id=round_obj.tenant_id, round=round_obj, teacher=teacher,
            starts_at=cursor, duration_minutes=duration_minutes, location=location[:150],
        ))
        cursor += timedelta(minutes=duration_minutes)
        since_break += 1
        if break_after and since_break >= break_after:
            cursor += timedelta(minutes=break_minutes)
            since_break = 0

    # ignore_conflicts so re-running for a teacher who already has part of the
    # evening laid out tops it up instead of failing on the first clash.
    InterviewSlot.objects.bulk_create(created, ignore_conflicts=True)
    return InterviewSlot.objects.filter(
        tenant_id=round_obj.tenant_id, round=round_obj, teacher=teacher,
        starts_at__gte=start, starts_at__lt=end,
    )


def available_slots(round_obj, *, teacher_id=None, student_id=None):
    """
    Slots a family can still take.

    Excludes anything already booked or blocked. Ordered by time, which is how
    a parent builds an evening — they pick a window, then see who is free in it.
    """
    slots = InterviewSlot.objects.filter(
        tenant_id=round_obj.tenant_id, round=round_obj, is_available=True
    ).select_related("teacher").order_by("starts_at")
    if teacher_id:
        slots = slots.filter(teacher_id=teacher_id)

    taken = set(
        InterviewBooking.objects.filter(
            tenant_id=round_obj.tenant_id, slot__round=round_obj, status="booked"
        ).values_list("slot_id", flat=True)
    )

    # A family's own bookings are shown so they can see their evening take
    # shape rather than losing track of what they have already taken.
    mine = {}
    if student_id:
        mine = {
            b.slot_id: b
            for b in InterviewBooking.objects.filter(
                tenant_id=round_obj.tenant_id, slot__round=round_obj,
                student_id=student_id, status="booked",
            )
        }

    rows = []
    for slot in slots:
        booked_by_me = slot.id in mine
        if slot.id in taken and not booked_by_me:
            continue
        rows.append({
            "slot": str(slot.id),
            "teacher": str(slot.teacher_id),
            "teacher_name": f"{slot.teacher.first_name} {slot.teacher.last_name}".strip(),
            "starts_at": slot.starts_at,
            "ends_at": slot.ends_at(),
            "duration_minutes": slot.duration_minutes,
            "location": slot.location,
            "booked_by_me": booked_by_me,
        })
    return rows


@transaction.atomic
def book(slot, *, student, booked_by_email="", booked_by_name="", note=""):
    """
    Take a slot for a student.

    The uniqueness constraint is what actually prevents a double booking; the
    check below only produces a better message in the common case. Relying on
    the check alone would lose the race it exists to prevent.
    """
    round_obj = slot.round
    now = timezone.now()

    if not round_obj.is_open(now):
        if not round_obj.is_published:
            raise InterviewError("This interview round is not open for bookings.")
        if now < round_obj.bookings_open_at:
            raise InterviewError(f"Bookings open at {round_obj.bookings_open_at:%d %b %H:%M}.")
        raise InterviewError("Bookings for this round have closed.")

    if not slot.is_available:
        raise InterviewError(slot.blocked_reason or "This time is not available.")

    existing = InterviewBooking.objects.filter(
        tenant_id=slot.tenant_id, slot__round=round_obj, student=student, status="booked"
    )
    if existing.filter(slot__teacher_id=slot.teacher_id).exists():
        raise InterviewError("You already have an appointment with this teacher.")
    if existing.count() >= round_obj.max_bookings_per_student:
        raise InterviewError(
            f"You already have {round_obj.max_bookings_per_student} appointments, which is "
            f"the limit for this round. Cancel one to book another."
        )

    # Two appointments at the same moment cannot both be attended.
    clash = existing.filter(slot__starts_at=slot.starts_at).first()
    if clash:
        raise InterviewError(
            f"You already have an appointment at {slot.starts_at:%H:%M} with "
            f"{clash.slot.teacher.first_name} {clash.slot.teacher.last_name}."
        )

    try:
        return InterviewBooking.objects.create(
            tenant_id=slot.tenant_id, slot=slot, student=student,
            booked_by_email=booked_by_email[:255], booked_by_name=booked_by_name[:255],
            note=note[:500], status="booked",
        )
    except IntegrityError:
        raise InterviewError("Someone just took that time. Please choose another.")


def cancel(booking):
    """Free the slot, keep the row."""
    if booking.status != "booked":
        raise InterviewError(f"This appointment is already {booking.status}.")
    booking.status = "cancelled"
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=["status", "cancelled_at", "updated_at"])
    return booking


def schedule_for_student(round_obj, student_id):
    """A family's evening, in order — what they print or screenshot."""
    bookings = InterviewBooking.objects.filter(
        tenant_id=round_obj.tenant_id, slot__round=round_obj,
        student_id=student_id, status="booked",
    ).select_related("slot", "slot__teacher").order_by("slot__starts_at")

    return [
        {
            "booking": str(b.id),
            "slot": str(b.slot_id),
            "teacher_name": f"{b.slot.teacher.first_name} {b.slot.teacher.last_name}".strip(),
            "starts_at": b.slot.starts_at,
            "ends_at": b.slot.ends_at(),
            "location": b.slot.location,
        }
        for b in bookings
    ]


def schedule_for_teacher(round_obj, teacher_id):
    """
    A teacher's evening, with the empty slots left in.

    Gaps are shown rather than compressed away: a teacher needs to know they
    have 6:20 free, both to pace the evening and because an unbooked slot next
    to a family they wanted to see is worth a phone call.
    """
    slots = InterviewSlot.objects.filter(
        tenant_id=round_obj.tenant_id, round=round_obj, teacher_id=teacher_id
    ).order_by("starts_at")
    bookings = {
        b.slot_id: b
        for b in InterviewBooking.objects.filter(
            tenant_id=round_obj.tenant_id, slot__round=round_obj,
            slot__teacher_id=teacher_id, status="booked",
        ).select_related("student")
    }

    rows = []
    for slot in slots:
        booking = bookings.get(slot.id)
        rows.append({
            "slot": str(slot.id),
            "starts_at": slot.starts_at,
            "ends_at": slot.ends_at(),
            "is_available": slot.is_available,
            "student": str(booking.student_id) if booking else None,
            "student_name": (
                f"{booking.student.first_name} {booking.student.last_name}".strip()
                if booking else None
            ),
            "booked_by": booking.booked_by_name or booking.booked_by_email if booking else "",
            "note": booking.note if booking else "",
        })
    return {
        "round": str(round_obj.id),
        "slots": len(rows),
        "booked": sum(1 for r in rows if r["student"]),
        "free": sum(1 for r in rows if not r["student"] and r["is_available"]),
        "schedule": rows,
    }
