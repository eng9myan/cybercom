"""
Statutory report builders. Each returns a list[dict] of rows (JSON-ready) that
the views can also render as CSV. Pure functions over tenant-scoped querysets so
they are directly unit-testable.

Coverage:
  - NCCD return (students with disability, level of adjustment)
  - Attendance return (per-student attendance rate over a date range)
  - NAPLAN participation (Year 3/5/7/9 cohort with USI + participation flag)
  - National census (ABS/ACARA demographics: Indigenous, LBOTE, parental SES)
"""

from decimal import Decimal, ROUND_HALF_UP

NAPLAN_YEARS = (3, 5, 7, 9)


def _campus_name(student):
    return student.campus.name if student.campus_id else ""


def nccd_return(tenant_id, collection_year):
    from products.cyed.compliance.models import NCCDRecord

    qs = NCCDRecord.objects.filter(tenant_id=tenant_id, collection_year=collection_year) \
        .select_related("student", "student__campus")
    rows = []
    for r in qs:
        s = r.student
        rows.append({
            "student_number": s.student_number,
            "surname": s.last_name,
            "given_name": s.first_name,
            "year_level": s.year_level,
            "campus": _campus_name(s),
            "category": r.category,
            "level_of_adjustment": r.level_of_adjustment,
            "imputed": r.imputed_disability,
        })
    return rows


def nccd_summary(tenant_id, collection_year):
    """Aggregate counts by (category, level) — the numbers the return totals."""
    from collections import Counter

    counts = Counter()
    for row in nccd_return(tenant_id, collection_year):
        counts[(row["category"], row["level_of_adjustment"])] += 1
    return [
        {"category": cat, "level_of_adjustment": lvl, "count": n}
        for (cat, lvl), n in sorted(counts.items())
    ]


def attendance_return(tenant_id, date_from=None, date_to=None):
    from products.cyed.attendance.models import AttendanceMark
    from products.cyed.sis.models import Student

    marks = AttendanceMark.objects.filter(tenant_id=tenant_id)
    if date_from:
        marks = marks.filter(roll_call__date__gte=date_from)
    if date_to:
        marks = marks.filter(roll_call__date__lte=date_to)

    # tally per student
    tally = {}
    for m in marks.values("student_id", "status"):
        t = tally.setdefault(m["student_id"], {"present": 0, "total": 0})
        t["total"] += 1
        if m["status"] in ("present", "late", "left_early"):
            t["present"] += 1

    rows = []
    students = {s.id: s for s in Student.objects.filter(tenant_id=tenant_id).select_related("campus")}
    for sid, t in tally.items():
        s = students.get(sid)
        if s is None:
            continue
        rate = Decimal("0")
        if t["total"]:
            rate = (Decimal(t["present"]) / Decimal(t["total"]) * 100).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP)
        rows.append({
            "student_number": s.student_number,
            "surname": s.last_name,
            "given_name": s.first_name,
            "year_level": s.year_level,
            "campus": _campus_name(s),
            "sessions_possible": t["total"],
            "sessions_attended": t["present"],
            "attendance_rate": str(rate),
        })
    rows.sort(key=lambda r: (r["year_level"], r["surname"]))
    return rows


def naplan_participation(tenant_id):
    from products.cyed.sis.models import Student

    qs = Student.objects.filter(
        tenant_id=tenant_id, year_level__in=NAPLAN_YEARS, enrolment_status="enrolled"
    ).select_related("campus").order_by("year_level", "last_name")
    rows = []
    for s in qs:
        rows.append({
            "usi": s.usi,
            "student_number": s.student_number,
            "surname": s.last_name,
            "given_name": s.first_name,
            "year_level": s.year_level,
            "campus": _campus_name(s),
            # participation defaults to expected 'P'; withdrawals/exemptions
            # are recorded by editing the export downstream in the NAP portal.
            "participation": "P",
            "lbote": s.lbote,
            "indigenous_status": s.indigenous_status,
        })
    return rows


def census(tenant_id):
    from products.cyed.sis.models import Student

    qs = Student.objects.filter(tenant_id=tenant_id, enrolment_status="enrolled") \
        .select_related("campus").order_by("year_level", "last_name")
    rows = []
    for s in qs:
        rows.append({
            "student_number": s.student_number,
            "state_student_number": s.state_student_number,
            "surname": s.last_name,
            "given_name": s.first_name,
            "date_of_birth": s.date_of_birth.isoformat() if s.date_of_birth else "",
            "gender": s.gender,
            "year_level": s.year_level,
            "campus": _campus_name(s),
            "indigenous_status": s.indigenous_status,
            "country_of_birth": s.country_of_birth,
            "language_at_home": s.language_at_home,
            "lbote": s.lbote,
            "parent1_school_education": s.parent1_school_education,
            "parent1_occupation_group": s.parent1_occupation_group,
            "parent2_school_education": s.parent2_school_education,
            "parent2_occupation_group": s.parent2_occupation_group,
        })
    return rows
