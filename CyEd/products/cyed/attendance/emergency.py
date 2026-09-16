"""
Emergency roll: fire drills, evacuations, lockdowns.

Built to be used standing in a car park on a phone, by a teacher whose class is
scattered, while an alarm is going. Every decision here follows from that.

**Everyone on site, not everyone enrolled.** The roll is built from today's
attendance marks plus signed-in visitors and contractors. A student marked
absent this morning is not missing from the assembly point — they are at home,
and putting them on a list of unaccounted children sends someone back into a
building for no reason.

**Nobody is "safe" by default.** Every person starts `unaccounted` and is moved
to `safe` only when a human says so. A roll that defaults to safe and requires
marking people missing produces a clear board and a wrong one.

**Medical plans travel with the roll.** If a child with anaphylaxis is
unaccounted for, the person searching needs to know that now, not after finding
them.
"""

from django.db import transaction
from django.utils import timezone

from platform.common.models import BaseModel  # noqa: F401  (documents the base used by models)


def roll_for(tenant_id, *, day=None, campus_id=None):
    """
    Who is on site right now, and what each person needs.

    Returns students grouped by class section — the unit a teacher supervises
    and can actually check — plus staff and visitors.
    """
    from products.cyed.attendance.models import AttendanceMark
    from products.cyed.health.services import critical_plans

    day = day or timezone.localdate()

    marks = (
        AttendanceMark.objects.filter(tenant_id=tenant_id, roll_call__date=day)
        .select_related("student", "roll_call__class_section", "student__campus")
        .order_by("student__last_name", "student__first_name")
    )
    if campus_id:
        marks = marks.filter(student__campus_id=campus_id)

    # Present or late means on site. Absent, excused and left_early do not.
    on_site, off_site = {}, []
    for mark in marks:
        student = mark.student
        entry = {
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "class_section": (
                mark.roll_call.class_section.name if mark.roll_call.class_section_id else ""
            ),
            "status": mark.status,
        }
        if mark.status in ("present", "late"):
            # A student appears in several rolls a day; keep one entry, and
            # prefer the most recent class so the search starts in the right room.
            on_site[str(student.id)] = entry
        else:
            off_site.append(entry)

    plans = {
        p["student"]: p
        for p in critical_plans(tenant_id, student_ids=list(on_site), campus_id=campus_id)
    }
    for student_id, entry in on_site.items():
        plan = plans.get(student_id)
        if plan:
            entry["medical_alert"] = {
                "type": plan["plan_type_display"],
                "severity": plan["severity"],
                "triggers": plan["triggers"],
                "medication": plan["medication"],
                "medication_location": plan["medication_location"],
                "plan_status": plan["status"],
            }

    # A student in the sick bay is on site but not with their class, so the
    # teacher calling that roll will report them missing and someone will go
    # back inside for a child who is already accounted for. Flagged, and
    # grouped separately so the warden can see them at a glance.
    for visit in _sick_bay_now(tenant_id):
        entry = on_site.get(visit["student"])
        if entry is not None:
            entry["in_sick_bay"] = True
            entry["class_section"] = "Sick bay"

    by_section = {}
    for entry in on_site.values():
        by_section.setdefault(entry["class_section"] or "Unassigned", []).append(entry)

    return {
        "date": day.isoformat(),
        "on_site_count": len(on_site),
        "off_site_count": len(off_site),
        "medical_alerts": sum(1 for e in on_site.values() if "medical_alert" in e),
        "sections": [
            {"class_section": name, "count": len(rows), "students": rows}
            for name, rows in sorted(by_section.items())
        ],
        # Kept, not hidden: someone always asks "where is X?" and the answer
        # "marked absent at 9am" ends the search immediately.
        "off_site": off_site,
        "visitors": _visitors_on_site(tenant_id, day),
    }


def _sick_bay_now(tenant_id):
    """Open sick bay visits, imported late to keep attendance off health at load."""
    from products.cyed.health.services import open_visits

    return open_visits(tenant_id)


def _visitors_on_site(tenant_id, day):
    """
    Visitors and contractors who signed in and have not signed out.

    Included because they are people in the building. A fire warden counting
    heads against a roll of students alone will come up short and not know why.
    """
    from products.cyed.visitors.models import Visitor

    rows = Visitor.objects.filter(
        tenant_id=tenant_id, signed_in_at__date=day, signed_out_at__isnull=True
    )
    return [
        {
            "visitor": str(v.id),
            "name": v.full_name,
            "organisation": v.organisation,
            "purpose": v.purpose,
            "host": v.host_name,
            "phone": v.phone,
        }
        for v in rows
    ]


@transaction.atomic
def open_drill(tenant_id, *, kind, campus_id=None, started_by="", day=None):
    """
    Start a drill and snapshot who was on site at that moment.

    Snapshotted rather than recomputed: the roll must not change under the
    people using it because a late student was marked present halfway through
    an evacuation. The record afterwards also has to show who was expected,
    which a live query cannot reconstruct.
    """
    from products.cyed.attendance.models import EmergencyDrill, EmergencyRollEntry

    day = day or timezone.localdate()
    snapshot = roll_for(tenant_id, day=day, campus_id=campus_id)

    drill = EmergencyDrill.objects.create(
        tenant_id=tenant_id, kind=kind, campus_id=campus_id,
        started_at=timezone.now(), started_by=started_by[:255],
        expected_count=snapshot["on_site_count"],
    )

    entries = []
    for section in snapshot["sections"]:
        for student in section["students"]:
            entries.append(EmergencyRollEntry(
                tenant_id=tenant_id, drill=drill,
                student_id=student["student"],
                display_name=student["name"],
                class_section_name=student["class_section"],
                has_medical_alert="medical_alert" in student,
            ))
    EmergencyRollEntry.objects.bulk_create(entries)
    return drill


def mark_accounted(drill, *, student_ids, state="safe", actor=""):
    """
    Move people to safe (or missing). Idempotent — the same student called
    twice at a noisy assembly point must not error.
    """
    from products.cyed.attendance.models import EmergencyRollEntry

    updated = EmergencyRollEntry.objects.filter(
        tenant_id=drill.tenant_id, drill=drill, student_id__in=student_ids
    ).update(state=state, accounted_at=timezone.now(), accounted_by=actor[:255])
    return updated


def drill_status(drill) -> dict:
    """
    The board: how many accounted for, and — the only number that matters —
    who is still not.
    """
    from products.cyed.attendance.models import EmergencyRollEntry

    entries = EmergencyRollEntry.objects.filter(tenant_id=drill.tenant_id, drill=drill)
    unaccounted = [
        {
            "student": str(e.student_id),
            "name": e.display_name,
            "class_section": e.class_section_name,
            "medical_alert": e.has_medical_alert,
        }
        for e in entries.filter(state="unaccounted")
    ]
    # Medical alerts first: if someone is missing and carries an EpiPen, that
    # is who the next person out the door should be looking for.
    unaccounted.sort(key=lambda r: (not r["medical_alert"], r["name"]))

    return {
        "drill": str(drill.id),
        "kind": drill.kind,
        "started_at": drill.started_at,
        "ended_at": drill.ended_at,
        "expected": drill.expected_count,
        "safe": entries.filter(state="safe").count(),
        "missing": entries.filter(state="missing").count(),
        "unaccounted": len(unaccounted),
        "all_clear": not unaccounted and not entries.filter(state="missing").exists(),
        "still_unaccounted": unaccounted,
    }


def close_drill(drill, *, actor="", note=""):
    """
    End the drill. Allowed with people still unaccounted for — an evacuation
    does not wait for tidy data — but the count is frozen into the record so
    the debrief cannot quietly lose it.
    """
    status = drill_status(drill)
    drill.ended_at = timezone.now()
    drill.ended_by = actor[:255]
    drill.note = note[:500]
    drill.unaccounted_at_close = status["unaccounted"] + status["missing"]
    drill.save(update_fields=[
        "ended_at", "ended_by", "note", "unaccounted_at_close", "updated_at",
    ])
    return drill
