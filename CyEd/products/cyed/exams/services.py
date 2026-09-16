"""
Seat allocation and hall tickets.

Allocation is deterministic and re-runnable: the same cohort and rooms always
produce the same plan, so a seating chart printed on Tuesday still matches the
hall on Thursday. Randomised seating would make that impossible to verify.

Order of placement matters and is the one interesting decision here. Candidates
with access arrangements go first — a separate-room arrangement into an
accessible room, then extra-time candidates grouped together so an invigilator
can manage one finish time per room rather than watching individual clocks.
Everyone else follows alphabetically, which is also how the door list reads.
"""

from django.db import transaction
from django.utils import timezone

from products.cyed.exams.models import ExamCandidate, ExamRoomAllocation


class ExamError(Exception):
    """An exam operation was refused for a business reason (→ HTTP 400/409)."""


# Arrangements that require a room of their own.
SEPARATE_ROOM_ARRANGEMENTS = {"separate_room", "reader", "scribe"}


def _placement_order(candidates):
    """
    Sort candidates into the order they should be seated.

    Separate-room arrangements first, then other arrangements, then everyone
    else — each group alphabetically so the result is stable and the door list
    is readable.
    """
    def key(candidate):
        if candidate.access_arrangement in SEPARATE_ROOM_ARRANGEMENTS:
            band = 0
        elif candidate.access_arrangement:
            band = 1
        else:
            band = 2
        student = candidate.student
        return (band, student.last_name.lower(), student.first_name.lower())

    return sorted(candidates, key=key)


@transaction.atomic
def allocate_seats(sitting):
    """
    Place every expected candidate into a seat.

    Refuses rather than partially seating when there are not enough desks: a
    plan that silently leaves six students unplaced is worse than no plan,
    because nobody discovers it until the morning of the exam.
    """
    allocations = list(
        ExamRoomAllocation.objects.select_related("room").filter(sitting=sitting)
    )
    if not allocations:
        raise ExamError("Book at least one room before allocating seats.")

    candidates = list(
        ExamCandidate.objects.select_related("student").filter(
            sitting=sitting, attendance__in=["expected", "present"]
        )
    )
    if not candidates:
        raise ExamError("No candidates are entered for this sitting.")

    capacity = sum(a.room.capacity for a in allocations)
    if len(candidates) > capacity:
        raise ExamError(
            f"{len(candidates)} candidates but only {capacity} seats across "
            f"{len(allocations)} room(s). Book another room."
        )

    # Accessible rooms first so separate-room arrangements land in one.
    allocations.sort(key=lambda a: (not a.room.is_accessible, a.room.name))
    seats = []
    for allocation in allocations:
        for label in allocation.room.seat_labels():
            seats.append((allocation.room, label))

    placed = []
    for candidate, (room, label) in zip(_placement_order(candidates), seats):
        candidate.room = room
        candidate.seat_label = label
        placed.append(candidate)

    # Clear old seating first: without this a re-run against a smaller room set
    # would collide with seats the previous plan still holds.
    ExamCandidate.objects.filter(sitting=sitting).update(room=None, seat_label="")
    ExamCandidate.objects.bulk_update(placed, ["room", "seat_label", "updated_at"])

    sitting.status = "seated"
    sitting.save(update_fields=["status", "updated_at"])
    return placed


def issue_tickets(sitting):
    """
    Issue a hall ticket to every seated candidate.

    Requires seating to exist: a ticket that does not name a seat is a piece of
    paper, and one issued before allocation would name a seat that changes.
    """
    candidates = list(ExamCandidate.objects.select_related("student", "room").filter(
        sitting=sitting, attendance__in=["expected", "present"]
    ))
    if not candidates:
        raise ExamError("No candidates are entered for this sitting.")
    unseated = [c for c in candidates if not c.seat_label]
    if unseated:
        raise ExamError(
            f"{len(unseated)} candidate(s) have no seat. Allocate seating before "
            f"issuing tickets."
        )

    now = timezone.now()
    for index, candidate in enumerate(candidates, start=1):
        if not candidate.ticket_number:
            candidate.ticket_number = f"{sitting.date:%Y%m%d}-{index:04d}"
        candidate.ticket_issued_on = now
    ExamCandidate.objects.bulk_update(
        candidates, ["ticket_number", "ticket_issued_on", "updated_at"]
    )
    return candidates


def hall_ticket(candidate) -> dict:
    """Everything printed on one student's ticket."""
    sitting = candidate.sitting
    student = candidate.student
    return {
        "ticket_number": candidate.ticket_number,
        "student": str(student.id),
        "student_name": f"{student.first_name} {student.last_name}".strip(),
        "student_number": student.student_number,
        "year_level": student.year_level,
        "exam": sitting.name,
        "subject": sitting.subject,
        "date": sitting.date.isoformat(),
        "start_time": sitting.start_time.isoformat() if sitting.start_time else None,
        "duration_minutes": sitting.duration_minutes + candidate.extra_time_minutes,
        "finish_time": (
            candidate.finish_time(sitting).isoformat() if candidate.finish_time(sitting) else None
        ),
        "room": candidate.room.name if candidate.room else None,
        "seat": candidate.seat_label,
        "access_arrangement": candidate.access_arrangement,
        "materials_permitted": sitting.materials_permitted,
        "instructions": sitting.instructions,
    }


def seating_chart(sitting) -> dict:
    """
    The plan an invigilator carries: room by room, seat by seat.

    Access arrangements are shown per candidate because the person supervising
    the room is the one who has to honour them.
    """
    rooms = {}
    for candidate in ExamCandidate.objects.select_related("student", "room").filter(
        sitting=sitting
    ).exclude(room__isnull=True):
        rooms.setdefault(candidate.room.name, []).append({
            "seat": candidate.seat_label,
            "student": str(candidate.student_id),
            "name": f"{candidate.student.first_name} {candidate.student.last_name}".strip(),
            "student_number": candidate.student.student_number,
            "access_arrangement": candidate.access_arrangement,
            "extra_time_minutes": candidate.extra_time_minutes,
            "attendance": candidate.attendance,
        })
    for seats in rooms.values():
        seats.sort(key=lambda s: s["seat"])

    invigilators = {
        a.room.name: (
            f"{a.invigilator.first_name} {a.invigilator.last_name}".strip()
            if a.invigilator else ""
        )
        for a in ExamRoomAllocation.objects.select_related("room", "invigilator").filter(
            sitting=sitting
        )
    }
    return {
        "sitting": str(sitting.id),
        "name": sitting.name,
        "date": sitting.date.isoformat(),
        "rooms": [
            {
                "room": name,
                "invigilator": invigilators.get(name, ""),
                "seated": len(seats),
                "seats": seats,
            }
            for name, seats in sorted(rooms.items())
        ],
        "unseated": ExamCandidate.objects.filter(sitting=sitting, room__isnull=True).count(),
    }


def attendance_register(sitting) -> dict:
    """Who turned up — the register signed in the hall."""
    rows = []
    for candidate in ExamCandidate.objects.select_related("student", "room").filter(
        sitting=sitting
    ):
        rows.append({
            "candidate": str(candidate.id),
            "student": str(candidate.student_id),
            "name": f"{candidate.student.first_name} {candidate.student.last_name}".strip(),
            "room": candidate.room.name if candidate.room else None,
            "seat": candidate.seat_label,
            "attendance": candidate.attendance,
        })
    rows.sort(key=lambda r: (r["room"] or "", r["seat"]))
    counts = {}
    for row in rows:
        counts[row["attendance"]] = counts.get(row["attendance"], 0) + 1
    return {"sitting": str(sitting.id), "count": len(rows), "by_status": counts, "results": rows}
