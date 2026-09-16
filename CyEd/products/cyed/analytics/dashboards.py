"""
School-wide analytics for executive leadership.

Everything here aggregates in SQL. These are the queries a principal opens on a
Monday across every campus at once, and the load test earlier in this project
showed exactly what happens when a report iterates in Python instead — a
household balance sweep took 104 seconds because it asked a question per row.

Three deliberate choices about *what* is reported:

**Rates, not raw counts.** A campus with 900 students will always have more
absences than one with 200. Comparing counts across a group tells leadership
nothing except which campus is biggest.

**Small cohorts are suppressed.** A "year level" of four students is one child's
attendance record with a label on it, and a group executive is not the right
audience for that. Cohorts below a floor report their size and withhold the
rate.

**Trends over points.** A single week's attendance is weather; the shape over a
term is climate. Every series here returns the history, not just today.
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Case, Count, F, IntegerField, Q, Sum, When
from django.db.models.functions import TruncWeek
from django.utils import timezone

# Below this, a cohort's rate is one or two children and is withheld. Chosen to
# match the threshold most Australian jurisdictions use for public reporting.
MIN_COHORT = 5

# Attendance statuses that count as attending. Late is attendance — a rate that
# penalised lateness twice would disagree with what the school reports to the
# department.
PRESENT_STATUSES = ["present", "late"]


def _rate(attended, total):
    if not total:
        return None
    return round(attended / total * 100, 1)


def attendance_trend(tenant_id, *, weeks=20, campus_id=None):
    """
    Weekly attendance rate across the school.

    Grouped in the database by week. A term of daily points is unreadable on a
    dashboard and hides the trend it exists to show.
    """
    from products.cyed.attendance.models import AttendanceMark

    since = timezone.localdate() - timedelta(weeks=weeks)
    marks = AttendanceMark.objects.filter(
        tenant_id=tenant_id, roll_call__date__gte=since
    )
    if campus_id:
        marks = marks.filter(student__campus_id=campus_id)

    rows = (
        marks.annotate(week=TruncWeek("roll_call__date"))
        .values("week")
        .annotate(
            total=Count("id"),
            attended=Count("id", filter=Q(status__in=PRESENT_STATUSES)),
        )
        .order_by("week")
    )
    return [
        {
            "week": row["week"].isoformat() if row["week"] else None,
            "total": row["total"],
            "attended": row["attended"],
            "rate": _rate(row["attended"], row["total"]),
        }
        for row in rows
    ]


def attendance_by_year_level(tenant_id, *, weeks=20, campus_id=None):
    """
    Where attendance is weakest. Usually the answer is one or two year levels,
    and knowing which is the difference between a policy and a conversation.
    """
    from products.cyed.attendance.models import AttendanceMark

    since = timezone.localdate() - timedelta(weeks=weeks)
    marks = AttendanceMark.objects.filter(
        tenant_id=tenant_id, roll_call__date__gte=since
    )
    if campus_id:
        marks = marks.filter(student__campus_id=campus_id)

    rows = (
        marks.values("student__year_level")
        .annotate(
            total=Count("id"),
            attended=Count("id", filter=Q(status__in=PRESENT_STATUSES)),
            students=Count("student_id", distinct=True),
        )
        .order_by("student__year_level")
    )
    out = []
    for row in rows:
        small = row["students"] < MIN_COHORT
        out.append({
            "year_level": row["student__year_level"],
            "students": row["students"],
            "total_marks": row["total"],
            # Withheld rather than shown: a rate over four students is one
            # child's record with a label on it.
            "rate": None if small else _rate(row["attended"], row["total"]),
            "suppressed": small,
        })
    return out


def chronic_absence(tenant_id, *, weeks=20, threshold=90, campus_id=None):
    """
    Students below an attendance threshold — the cohort schools are held to
    account for, and the one that turns a trend line into a list of names.

    Counted per student in SQL. Ninety per cent is the conventional Australian
    line for "at risk"; it is a parameter because jurisdictions differ.
    """
    from products.cyed.attendance.models import AttendanceMark

    since = timezone.localdate() - timedelta(weeks=weeks)
    marks = AttendanceMark.objects.filter(
        tenant_id=tenant_id, roll_call__date__gte=since,
        student__enrolment_status="enrolled",
    )
    if campus_id:
        marks = marks.filter(student__campus_id=campus_id)

    rows = (
        marks.values(
            "student_id", "student__first_name", "student__last_name", "student__year_level"
        )
        .annotate(
            total=Count("id"),
            attended=Count("id", filter=Q(status__in=PRESENT_STATUSES)),
        )
        # A handful of marks is not a rate; it is a student who enrolled last week.
        .filter(total__gte=10)
    )

    out = []
    for row in rows:
        rate = _rate(row["attended"], row["total"])
        if rate is None or rate >= threshold:
            continue
        out.append({
            "student": str(row["student_id"]),
            "name": f"{row['student__first_name']} {row['student__last_name']}".strip(),
            "year_level": row["student__year_level"],
            "rate": rate,
            "sessions": row["total"],
            "missed": row["total"] - row["attended"],
        })
    out.sort(key=lambda r: r["rate"])
    return {"threshold": threshold, "count": len(out), "results": out}


def achievement_distribution(tenant_id, *, year_level=None, campus_id=None):
    """
    The spread of A–E across the school.

    A distribution, not an average: "the school averages a C" is a number that
    hides both the students failing and the ones coasting.
    """
    from products.cyed.gradebook.models import Grade

    grades = Grade.objects.filter(tenant_id=tenant_id).exclude(achievement_level="")
    if year_level:
        grades = grades.filter(student__year_level=year_level)
    if campus_id:
        grades = grades.filter(student__campus_id=campus_id)

    rows = (
        grades.values("achievement_level")
        .annotate(count=Count("id"))
        .order_by("achievement_level")
    )
    total = sum(r["count"] for r in rows)
    return {
        "total": total,
        "distribution": [
            {
                "level": row["achievement_level"],
                "count": row["count"],
                "percent": round(row["count"] / total * 100, 1) if total else 0,
            }
            for row in rows
        ],
    }


def behaviour_summary(tenant_id, *, weeks=20, campus_id=None):
    """
    Merit and demerit activity over time.

    Positive and negative are reported side by side on purpose: a behaviour
    dashboard that counts only incidents tells a school it is getting worse
    even when recognition is rising faster.
    """
    from products.cyed.wellbeing.models import BehaviourIncident

    since = timezone.localdate() - timedelta(weeks=weeks)
    incidents = BehaviourIncident.objects.filter(tenant_id=tenant_id, date__gte=since)
    if campus_id:
        incidents = incidents.filter(student__campus_id=campus_id)

    weekly = (
        incidents.annotate(week=TruncWeek("date"))
        .values("week")
        .annotate(
            positive=Count("id", filter=Q(category="positive")),
            minor=Count("id", filter=Q(category="minor")),
            major=Count("id", filter=Q(category="major")),
        )
        .order_by("week")
    )
    return {
        "weeks": [
            {
                "week": row["week"].isoformat() if row["week"] else None,
                "positive": row["positive"],
                "minor": row["minor"],
                "major": row["major"],
            }
            for row in weekly
        ],
        "by_year_level": list(
            incidents.values("student__year_level")
            .annotate(
                positive=Count("id", filter=Q(category="positive")),
                negative=Count("id", filter=Q(category__in=["minor", "major"])),
            )
            .order_by("student__year_level")
        ),
    }


def campus_comparison(tenant_id, *, weeks=20):
    """
    Every campus side by side — the view that only matters to a group.

    Rates throughout, because a campus with 900 students will always post more
    absences than one with 200, and ranking on counts just ranks on size.
    """
    from products.cyed.attendance.models import AttendanceMark
    from products.cyed.org.models import Campus
    from products.cyed.sis.models import Student

    since = timezone.localdate() - timedelta(weeks=weeks)

    enrolled = dict(
        Student.objects.filter(tenant_id=tenant_id, enrolment_status="enrolled")
        .values_list("campus_id")
        .annotate(n=Count("id"))
    )
    attendance = {
        row["student__campus_id"]: row
        for row in AttendanceMark.objects.filter(
            tenant_id=tenant_id, roll_call__date__gte=since
        )
        .values("student__campus_id")
        .annotate(
            total=Count("id"),
            attended=Count("id", filter=Q(status__in=PRESENT_STATUSES)),
        )
    }

    rows = []
    for campus in Campus.objects.filter(tenant_id=tenant_id):
        stats = attendance.get(campus.id, {})
        students = enrolled.get(campus.id, 0)
        rows.append({
            "campus": str(campus.id),
            "name": campus.name,
            "students": students,
            "attendance_rate": (
                None if students < MIN_COHORT
                else _rate(stats.get("attended", 0), stats.get("total", 0))
            ),
            "suppressed": students < MIN_COHORT,
        })
    rows.sort(key=lambda r: (r["attendance_rate"] is None, r["attendance_rate"]))
    return rows


def overview(tenant_id, *, weeks=20, campus_id=None):
    """
    The single screen: how attendance is trending, where it is weakest, how
    many students are below the line, and what behaviour looks like.
    """
    trend = attendance_trend(tenant_id, weeks=weeks, campus_id=campus_id)
    recent = [w for w in trend if w["rate"] is not None][-4:]
    return {
        "weeks": weeks,
        "attendance_rate_recent": (
            round(sum(w["rate"] for w in recent) / len(recent), 1) if recent else None
        ),
        "attendance_trend": trend,
        "attendance_by_year_level": attendance_by_year_level(
            tenant_id, weeks=weeks, campus_id=campus_id
        ),
        "chronic_absence": chronic_absence(tenant_id, weeks=weeks, campus_id=campus_id),
        "achievement": achievement_distribution(tenant_id, campus_id=campus_id),
        "behaviour": behaviour_summary(tenant_id, weeks=weeks, campus_id=campus_id),
    }
