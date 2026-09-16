"""
Teacher substitution engine.

When a teacher is absent, find their timetabled classes for the day and propose
a free colleague for each. Transparent and deterministic; surfaces uncovered
gaps for a human to resolve rather than silently leaving a class unattended.

**This used to match teachers by name string**, which is the §0 finding the
workflow audit opened with. The consequences were not theoretical: "A. Nguyen"
and "Anh Nguyen" were different people, two staff sharing a surname were the
same person, and a rename orphaned a teacher's entire load. The engine now
reasons about `hr.Staff` — the names are kept only as the printed record.

Two rules the string version could not express at all:

* A colleague without a current WWCC or teacher registration is **not** in the
  cover pool. Cover is exactly the situation where an uncleared adult ends up
  in front of a class at short notice, so the clearance check belongs here.
* Someone who is themselves absent cannot cover. Obvious, and impossible to
  check when the pool was built from timetable strings.
"""

from products.cyed.substitution.models import SubstitutionAssignment, SubstitutionPlan


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    if not all([a_start, a_end, b_start, b_end]):
        return True  # missing times → assume a clash (conservative)
    return a_start < b_end and b_start < a_end


def _staff_absent_on(tenant_id, date):
    """Staff already known to be away that day — they cannot cover."""
    if date is None:
        return set()
    from products.cyed.staff_attendance.models import StaffAttendanceDay

    return set(
        StaffAttendanceDay.objects.filter(
            tenant_id=tenant_id, date=date,
            status__in=["absent", "leave", "sick"],
        ).values_list("staff_id", flat=True)
    )


def cover_pool(tenant_id, *, exclude_staff_id=None, date=None):
    """
    Staff eligible to cover a class, with the reason any were excluded.

    Returns (eligible, excluded) so the caller can explain a gap instead of
    reporting a bare "uncovered" that a human then has to investigate.
    """
    from products.cyed.hr.compliance import may_teach
    from products.cyed.hr.models import Staff

    away = _staff_absent_on(tenant_id, date)
    eligible, excluded = [], []
    for staff in Staff.objects.filter(
        tenant_id=tenant_id, is_active=True
    ).prefetch_related("clearances").order_by("last_name", "first_name"):
        if exclude_staff_id and staff.id == exclude_staff_id:
            continue
        if staff.id in away:
            excluded.append((staff, "already absent"))
            continue
        if not may_teach(staff):
            excluded.append((staff, "clearance not current"))
            continue
        eligible.append(staff)
    return eligible, excluded


def _is_free(tenant_id, staff, day_of_week, slot):
    """No other class in an overlapping window that day."""
    from products.cyed.timetable.models import TimetableSlot

    others = TimetableSlot.objects.filter(
        tenant_id=tenant_id, teacher_id=staff.id, day_of_week=day_of_week
    )
    for other in others:
        if other.id == slot.id:
            continue
        if _overlaps(slot.start_time, slot.end_time, other.start_time, other.end_time):
            return False
    return True


def _resolve_absent(tenant_id, absent_teacher, absent_staff):
    """
    Accept either a Staff record or a legacy name.

    Name lookup is a migration convenience, and deliberately refuses to guess
    when a name matches two people — silently picking one would reintroduce
    the exact bug this rewrite removes.
    """
    from products.cyed.hr.models import Staff

    if absent_staff is not None:
        return absent_staff, f"{absent_staff.first_name} {absent_staff.last_name}".strip()

    if not absent_teacher:
        return None, ""

    parts = absent_teacher.strip().split()
    matches = Staff.objects.filter(tenant_id=tenant_id, is_active=True)
    if len(parts) >= 2:
        matches = matches.filter(first_name__iexact=parts[0], last_name__iexact=parts[-1])
    else:
        matches = matches.filter(last_name__iexact=absent_teacher.strip())
    found = list(matches[:2])
    if len(found) == 1:
        return found[0], absent_teacher
    # Ambiguous or unknown: fall back to the name, which still finds legacy
    # slots that were never linked to a Staff record.
    return None, absent_teacher


def build_plan(tenant_id, *, absent_teacher="", absent_staff=None, day_of_week,
               date=None, generated_by=""):
    """
    Propose cover for every class the absent teacher was due to take.

    Load is balanced across the plan so one willing colleague does not absorb
    the whole day, and candidates are ordered deterministically so re-running
    produces the same sheet.
    """
    from products.cyed.timetable.models import TimetableSlot

    staff, display_name = _resolve_absent(tenant_id, absent_teacher, absent_staff)

    plan = SubstitutionPlan.objects.create(
        tenant_id=tenant_id, absent_teacher=display_name, absent_staff=staff,
        day_of_week=day_of_week, date=date, generated_by=generated_by,
    )

    slots = TimetableSlot.objects.select_related("class_section").filter(
        tenant_id=tenant_id, day_of_week=day_of_week
    )
    if staff is not None:
        # Slots assigned to them directly, plus slots that inherit the teacher
        # from their class section — a timetable row often leaves it implicit.
        slots = slots.filter(teacher_id=staff.id) | slots.filter(
            teacher__isnull=True, class_section__teacher_id=staff.id
        )
    else:
        slots = slots.filter(teacher__isnull=True, teacher_name=display_name)
    slots = slots.distinct().order_by("start_time")

    eligible, excluded = cover_pool(
        tenant_id, exclude_staff_id=staff.id if staff else None, date=date
    )
    load = {s.id: 0 for s in eligible}

    for slot in slots:
        candidates = [s for s in eligible if _is_free(tenant_id, s, day_of_week, slot)]
        # Fewest covers first, then name — stable across re-runs.
        candidates.sort(key=lambda s: (load[s.id], s.last_name.lower(), s.first_name.lower()))
        chosen = candidates[0] if candidates else None

        if chosen is not None:
            load[chosen.id] += 1
            gap_reason = ""
        elif not eligible:
            gap_reason = (
                f"No eligible staff: {len(excluded)} excluded "
                f"({', '.join(sorted({r for _s, r in excluded}))})."
                if excluded else "No other active staff to draw on."
            )
        else:
            gap_reason = "Every eligible colleague is teaching in this window."

        SubstitutionAssignment.objects.create(
            tenant_id=tenant_id, plan=plan, timetable_slot=slot,
            class_section_name=getattr(slot.class_section, "name", ""),
            period_label=slot.period_label, start_time=slot.start_time, end_time=slot.end_time,
            room=slot.room,
            original_teacher=display_name, original_staff=staff,
            substitute_teacher=(
                f"{chosen.first_name} {chosen.last_name}".strip() if chosen else ""
            ),
            substitute_staff=chosen,
            covered=chosen is not None,
            gap_reason=gap_reason,
        )
    return plan
