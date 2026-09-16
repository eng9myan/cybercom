"""
Merit and demerit points over the existing behaviour records.

`BehaviourIncident` recorded what happened but carried no points, so a school
running a merit system had to keep it on paper alongside. Adding a signed
`points` field to the record that already exists — rather than a parallel
merits table — means the tally and the incident log can never disagree about
what a child was given and why.

Totals are always computed from the incidents. A stored running total is a
number that drifts the first time an incident is amended or deleted, and a
drifted merit tally is one a fifteen-year-old will notice and dispute.
"""

from django.db.models import Count, Q, Sum
from django.utils import timezone

from products.cyed.wellbeing.models import BehaviourIncident


def _window(qs, date_from=None, date_to=None):
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    return qs


def student_tally(student, *, date_from=None, date_to=None) -> dict:
    """One student's merit position, and the incidents behind it."""
    qs = _window(
        BehaviourIncident.objects.filter(tenant_id=student.tenant_id, student=student),
        date_from, date_to,
    )
    totals = qs.aggregate(
        net=Sum("points"),
        merits=Sum("points", filter=Q(points__gt=0)),
        demerits=Sum("points", filter=Q(points__lt=0)),
        incidents=Count("id"),
    )
    return {
        "student": str(student.id),
        "name": f"{student.first_name} {student.last_name}".strip(),
        "year_level": student.year_level,
        "merits": totals["merits"] or 0,
        # Reported as a positive magnitude — "12 demerits" reads better than
        # "-12 demerits", and the sign is already carried by `net`.
        "demerits": abs(totals["demerits"] or 0),
        "net": totals["net"] or 0,
        "incidents": totals["incidents"] or 0,
    }


def leaderboard(tenant_id, *, date_from=None, date_to=None, year_level=None, limit=50):
    """
    Students by net points, best first.

    Ties break on fewest incidents, so a student who earned the same score in
    fewer interventions ranks higher — otherwise the ordering is arbitrary and
    changes between requests, which students notice.
    """
    from products.cyed.sis.models import Student

    qs = _window(
        BehaviourIncident.objects.filter(tenant_id=tenant_id), date_from, date_to
    )
    if year_level:
        qs = qs.filter(student__year_level=year_level)

    rows = (
        qs.values("student_id")
        .annotate(
            net=Sum("points"),
            merits=Sum("points", filter=Q(points__gt=0)),
            demerits=Sum("points", filter=Q(points__lt=0)),
            incidents=Count("id"),
        )
        .order_by("-net", "incidents")[:limit]
    )
    students = {
        s.id: s for s in Student.objects.filter(
            tenant_id=tenant_id, id__in=[r["student_id"] for r in rows]
        )
    }
    out = []
    for row in rows:
        student = students.get(row["student_id"])
        if student is None:
            continue
        out.append({
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "merits": row["merits"] or 0,
            "demerits": abs(row["demerits"] or 0),
            "net": row["net"] or 0,
            "incidents": row["incidents"],
        })
    return out


def house_standings(tenant_id, *, date_from=None, date_to=None):
    """
    House totals — the scoreboard a merit system exists to produce.

    Incidents with no house recorded are grouped under "Unassigned" rather than
    dropped: a missing house is a data-entry gap the school should see, not
    points that quietly vanish.
    """
    qs = _window(BehaviourIncident.objects.filter(tenant_id=tenant_id), date_from, date_to)
    rows = (
        qs.values("house")
        .annotate(
            net=Sum("points"),
            merits=Sum("points", filter=Q(points__gt=0)),
            demerits=Sum("points", filter=Q(points__lt=0)),
            incidents=Count("id"),
        )
        .order_by("-net")
    )
    return [
        {
            "house": row["house"] or "Unassigned",
            "merits": row["merits"] or 0,
            "demerits": abs(row["demerits"] or 0),
            "net": row["net"] or 0,
            "incidents": row["incidents"],
        }
        for row in rows
    ]


def award_bulk(tenant_id, *, student_ids, category, points=None, description="",
               reported_by="", date=None, house=""):
    """
    Give the same recognition to a group — the whole class that ran the
    assembly, the team that won the debate.

    One request, because a teacher awarding thirty merits one at a time simply
    will not do it.
    """
    date = date or timezone.localdate()
    rows = [
        BehaviourIncident(
            tenant_id=tenant_id, student_id=student_id, date=date, category=category,
            description=description, reported_by=reported_by, house=house,
            points=points if points is not None else BehaviourIncident.DEFAULT_POINTS.get(category, 0),
        )
        for student_id in student_ids
    ]
    # bulk_create skips save(), so the default-points fallback above is applied
    # explicitly here rather than relying on the model hook.
    return BehaviourIncident.objects.bulk_create(rows)
