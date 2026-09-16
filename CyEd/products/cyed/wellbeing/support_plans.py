"""
Support plan (IEP) lifecycle and the NCCD evidence it produces.

The reason this module exists rather than a few extra fields: NCCD is an
evidence collection, not a form. A school reporting "substantial adjustment"
for a student has to be able to show what was adjusted, who provided it, and
that it was reviewed with the family. Deriving the return from the plan means
those two can never disagree — which is the failure a separate NCCD table
invites, because somebody updates one and not the other.
"""

from django.db import transaction
from django.utils import timezone

from products.cyed.wellbeing.models import SupportPlan


class SupportPlanError(Exception):
    """A plan action was refused for a business reason (→ HTTP 400/409)."""


@transaction.atomic
def activate(plan, *, actor=""):
    """
    Put a plan in force, superseding any earlier active plan of the same type.

    Superseded rather than deleted or overwritten: "what was in force last
    March" is the question asked when something has gone wrong, and a plan
    edited in place cannot answer it.
    """
    if plan.status == "active":
        raise SupportPlanError("This plan is already active.")
    if plan.status in ("superseded", "closed"):
        raise SupportPlanError(f"A {plan.status} plan cannot be reactivated. Create a new one.")

    if not plan.adjustments.exists():
        # A plan with no adjustments is a document that changes nothing, and
        # reporting it to NCCD would be a claim the school cannot support.
        raise SupportPlanError(
            "Add at least one adjustment before activating — a plan with no "
            "adjustments is not evidence of support."
        )

    previous = SupportPlan.objects.filter(
        tenant_id=plan.tenant_id, student=plan.student,
        plan_type=plan.plan_type, status="active",
    ).exclude(pk=plan.pk)
    for old in previous:
        old.status = "superseded"
        old.superseded_by = plan
        old.save(update_fields=["status", "superseded_by", "updated_at"])

    plan.status = "active"
    plan.start_date = plan.start_date or timezone.localdate()
    plan.save(update_fields=["status", "start_date", "updated_at"])

    # Keep the learner profile flag true so existing screens and the adaptive
    # engine keep working — it is now derived from a real plan rather than
    # being the only record that one exists.
    _sync_profile_flag(plan.student)
    return plan


def close(plan, *, reason, actor=""):
    """Close a plan — the student no longer needs it, or has left."""
    if plan.status == "closed":
        raise SupportPlanError("This plan is already closed.")
    if not (reason or "").strip():
        raise SupportPlanError("Record why the plan is being closed.")

    plan.status = "closed"
    plan.closed_on = timezone.localdate()
    plan.closed_reason = reason.strip()[:255]
    plan.save(update_fields=["status", "closed_on", "closed_reason", "updated_at"])
    _sync_profile_flag(plan.student)
    return plan


def _sync_profile_flag(student):
    """
    Keep `LearnerProfile.has_individual_plan` in step with reality.

    The flag stays because other code reads it, but it is no longer the source
    of truth — it is now a cached answer to "does this student have an active
    plan", which the plans themselves decide.
    """
    from products.cyed.wellbeing.models import LearnerProfile

    has_plan = SupportPlan.objects.filter(
        tenant_id=student.tenant_id, student=student, status="active"
    ).exists()
    LearnerProfile.objects.filter(
        tenant_id=student.tenant_id, student=student
    ).update(has_individual_plan=has_plan)


def record_review(plan, *, held_on, participants, family_present=False,
                  student_present=False, discussion="", outcome="",
                  next_review_due=None, recorded_by=""):
    """
    Record a review meeting and roll the plan's next review date forward.

    Setting `review_due` from the meeting rather than a fixed calendar means
    the date always reflects what the people in the room agreed, which is what
    the family was told.
    """
    from products.cyed.wellbeing.models import SupportPlanReview

    if not (participants or "").strip():
        raise SupportPlanError(
            "Record who attended. A review with no participants is not evidence "
            "that one happened."
        )

    review = SupportPlanReview.objects.create(
        tenant_id=plan.tenant_id, plan=plan, held_on=held_on,
        participants=participants[:500], family_present=family_present,
        student_present=student_present, discussion=discussion,
        outcome=outcome[:500], next_review_due=next_review_due,
        recorded_by=recorded_by[:255],
    )
    if next_review_due:
        plan.review_due = next_review_due
        plan.save(update_fields=["review_due", "updated_at"])
    return review


def plans_needing_review(tenant_id, *, as_at=None):
    """Overdue or soon-due plans — the coordinator's worklist."""
    as_at = as_at or timezone.localdate()
    rows = []
    for plan in SupportPlan.objects.filter(
        tenant_id=tenant_id, status="active", student__enrolment_status="enrolled"
    ).select_related("student", "coordinator"):
        state = plan.review_state(as_at)
        if state == "current":
            continue
        rows.append({
            "plan": str(plan.id),
            "student": str(plan.student_id),
            "name": f"{plan.student.first_name} {plan.student.last_name}".strip(),
            "plan_type": plan.plan_type,
            "review_due": plan.review_due.isoformat() if plan.review_due else None,
            "state": state,
            "days_overdue": (
                (as_at - plan.review_due).days if plan.review_due and plan.review_due < as_at else 0
            ),
            "coordinator": (
                f"{plan.coordinator.first_name} {plan.coordinator.last_name}".strip()
                if plan.coordinator_id else ""
            ),
            "last_review": (
                plan.reviews.first().held_on.isoformat() if plan.reviews.exists() else None
            ),
        })
    order = {"overdue": 0, "no_review_date": 1, "due_soon": 2}
    rows.sort(key=lambda r: (order.get(r["state"], 9), -r["days_overdue"]))
    return rows


def nccd_evidence(tenant_id, *, year=None):
    """
    The NCCD return, derived from the plans that are actually in force.

    Each row carries the adjustment level *and* what it was based on, so the
    number reported can be traced to the adjustments and the review that
    justify it. A return typed in separately cannot be.
    """
    year = year or timezone.localdate().year
    rows = []
    for plan in SupportPlan.objects.filter(
        tenant_id=tenant_id, status="active"
    ).select_related("student").prefetch_related("adjustments", "reviews"):
        level = plan.highest_adjustment()
        if not level:
            continue
        adjustments = [a for a in plan.adjustments.all() if a.is_active]
        last_review = plan.reviews.first()
        rows.append({
            "student": str(plan.student_id),
            "name": f"{plan.student.first_name} {plan.student.last_name}".strip(),
            "year_level": plan.student.year_level,
            "adjustment_level": level,
            "adjustment_count": len(adjustments),
            "categories": sorted({a.category for a in adjustments}),
            "family_consulted_on": (
                plan.family_consulted_on.isoformat() if plan.family_consulted_on else None
            ),
            "last_review": last_review.held_on.isoformat() if last_review else None,
            # The three things that make a row defensible. Surfaced rather than
            # silently excluded: a school needs to see which of its claims are
            # thin before an auditor does.
            "evidence_complete": bool(
                adjustments and plan.family_consulted_on and last_review
            ),
        })
    rows.sort(key=lambda r: (not r["evidence_complete"], r["name"]))
    return {
        "year": year,
        "count": len(rows),
        "incomplete_evidence": sum(1 for r in rows if not r["evidence_complete"]),
        "by_level": _count_by(rows, "adjustment_level"),
        "results": rows,
    }


def _count_by(rows, key):
    counts = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return counts
