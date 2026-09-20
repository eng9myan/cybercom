"""
Composes the family-facing bridge summary from data that already exists
elsewhere in the product — see this app's models.py docstring for why
learning targets/progress are derived here, not duplicated into a new model.
"""
from datetime import timedelta

from django.utils import timezone

UPCOMING_WINDOW_DAYS = 14
RECENT_GRADES_LIMIT = 15


def _sections_for_student(tenant_id, student_id):
    from products.cyed.sis.models import Enrolment

    return set(
        Enrolment.objects.filter(
            tenant_id=tenant_id, student_id=student_id, status="active"
        ).values_list("class_section_id", flat=True)
    )


def _assignment_alerts(tenant_id, student):
    """Missed (overdue, not handed in) and upcoming (due soon) assignments."""
    from products.cyed.assessment.models import Assignment, Submission

    sections = _sections_for_student(tenant_id, student.id)
    assignments = Assignment.objects.filter(
        tenant_id=tenant_id, is_published=True, class_section_id__in=sections,
        due_at__isnull=False,
    ).select_related("class_section")

    submitted_ids = set(
        Submission.objects.filter(
            tenant_id=tenant_id, student=student, assignment__in=assignments,
            status__in=Submission.HANDED_IN,
        ).values_list("assignment_id", flat=True)
    )

    now = timezone.now()
    horizon = now + timedelta(days=UPCOMING_WINDOW_DAYS)
    missed, upcoming = [], []
    for a in assignments:
        if a.id in submitted_ids:
            continue
        row = {
            "id": str(a.id),
            "title": a.title,
            "class_section": a.class_section.name,
            "due_at": a.due_at.isoformat(),
            "curriculum_code": a.curriculum_code or None,
        }
        if a.due_at < now:
            missed.append(row)
        elif a.due_at <= horizon:
            upcoming.append(row)

    missed.sort(key=lambda r: r["due_at"])
    upcoming.sort(key=lambda r: r["due_at"])
    return missed, upcoming


def _learning_progress(tenant_id, student):
    """Recent grades, each tagged with the ACARA content-description code
    its assessment maps to when one is set — the "learning targets and
    progress" a family actually wants to see, not a synthetic goal object."""
    from products.cyed.gradebook.models import Grade

    grades = (
        Grade.objects.filter(tenant_id=tenant_id, student=student)
        .select_related("assessment", "assessment__class_section")
        .order_by("-created_at")[:RECENT_GRADES_LIMIT]
    )
    return [
        {
            "assessment": g.assessment.name,
            "class_section": g.assessment.class_section.name,
            "curriculum_code": g.assessment.curriculum_code or None,
            "score": str(g.score) if g.score is not None else None,
            "max_score": str(g.assessment.max_score),
            "achievement_level": g.achievement_level or None,
        }
        for g in grades
    ]


def _resources_for(tenant_id, student):
    from products.cyed.learning_bridge.models import FamilyResource

    qs = FamilyResource.objects.filter(
        tenant_id=tenant_id, is_published=True,
        year_level_min__lte=student.year_level, year_level_max__gte=student.year_level,
    )
    rows = list(qs)
    # Rank a language match first — never exclude general resources for a
    # family whose home language isn't recorded or doesn't match anything.
    home_language = (student.language_at_home or "").strip().lower()
    if home_language:
        rows.sort(key=lambda r: r.language.strip().lower() != home_language)
    return rows


def _packs_for(tenant_id, student):
    from products.cyed.learning_bridge.models import OfflineActivityPack

    return list(OfflineActivityPack.objects.filter(
        tenant_id=tenant_id, is_published=True,
        year_level_min__lte=student.year_level, year_level_max__gte=student.year_level,
    ))


def bridge_summary(tenant_id, student):
    missed, upcoming = _assignment_alerts(tenant_id, student)
    return {
        "student": str(student.id),
        "student_name": f"{student.first_name} {student.last_name}",
        "missed_assignments": missed,
        "upcoming_assignments": upcoming,
        "learning_progress": _learning_progress(tenant_id, student),
        "resources": _resources_for(tenant_id, student),
        "offline_packs": _packs_for(tenant_id, student),
    }
