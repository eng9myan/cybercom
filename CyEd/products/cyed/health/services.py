"""
Health duty-of-care rules.

Two obligations a school cannot discharge with a text field:

**Immunisation.** Enrolment requires a sighted AIR statement, and during an
outbreak of a vaccine-preventable disease a public-health directive can require
unimmunised children to be excluded. Both need a register that can be queried
per disease, not a note on a record.

**Medication.** A school administering prescribed medication must record each
dose — what, to whom, by whom, when. The record only means something if the
system also refuses the doses that should not happen: no authority, expired
authority, over the daily maximum, or inside the minimum interval. A log that
accepts anything documents the incident rather than preventing it.
"""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from products.cyed.health.models import (
    ActionPlan,
    ImmunisationRecord,
    MedicationAdministration,
    MedicationAuthority,
)
from products.cyed.sis.models import Student


class SickBayError(Exception):
    """A sick bay action was refused for a business reason (→ HTTP 400/409)."""


def open_visits(tenant_id, *, campus_id=None):
    """
    Who is in the sick bay right now.

    The question a first-aid officer is asked all day, and the one the
    emergency roll needs: a child lying down in the sick bay is exactly who
    nobody thinks to look for at an assembly point.
    """
    from products.cyed.health.models import SickBayVisit

    visits = SickBayVisit.objects.filter(
        tenant_id=tenant_id, departed_at__isnull=True
    ).select_related("student", "seen_by")
    if campus_id:
        visits = visits.filter(student__campus_id=campus_id)

    rows = []
    for visit in visits:
        student = visit.student
        rows.append({
            "visit": str(visit.id),
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "arrived_at": visit.arrived_at,
            "minutes_present": visit.minutes_present(),
            "complaint": visit.complaint,
            "referred_by": visit.referred_by,
            "guardians_notified": visit.guardians_notified,
            # Surfaced here because a child with a known condition presenting
            # unwell is a different situation from one who tripped over.
            "has_action_plan": ActionPlan.objects.filter(
                tenant_id=tenant_id, student=student, is_active=True
            ).exists(),
        })
    rows.sort(key=lambda r: r["arrived_at"])
    return rows


def close_visit(visit, *, outcome, treatment="", observations="", collected_by="",
                seen_by=None, notify=True):
    """
    Close a visit and tell the guardians if the outcome warrants it.

    Notification is driven by the outcome rather than a separate checkbox: a
    child being collected or an ambulance being called are the two cases where
    somebody has to be told now, and leaving that to a person to remember is
    what made the old `parent_notified` boolean meaningless.
    """
    from products.cyed.health.models import SickBayVisit

    if not visit.is_open():
        raise SickBayError("This visit has already been closed.")
    valid = {c[0] for c in SickBayVisit.OUTCOME_CHOICES}
    if outcome not in valid or outcome == "in_progress":
        raise SickBayError(
            f"'{outcome}' is not a closing outcome. Use one of: "
            f"{', '.join(sorted(valid - {'in_progress'}))}."
        )
    if outcome == "sent_home" and not (collected_by or "").strip():
        # A child released to nobody in particular is a safeguarding failure,
        # and this is the field a school will be asked for afterwards.
        raise SickBayError("Record who collected the student.")

    visit.outcome = outcome
    visit.departed_at = timezone.now()
    visit.treatment = treatment or visit.treatment
    visit.observations = observations or visit.observations
    visit.collected_by = collected_by[:255]
    if seen_by is not None:
        visit.seen_by = seen_by

    sent = 0
    if notify and outcome in SickBayVisit.NOTIFY_OUTCOMES:
        sent = notify_guardians(visit, outcome)
        visit.guardians_notified = sent
        visit.notified_at = timezone.now()

    visit.save(update_fields=[
        "outcome", "departed_at", "treatment", "observations", "collected_by",
        "seen_by", "guardians_notified", "notified_at", "updated_at",
    ])
    return visit


def notify_guardians(visit, outcome) -> int:
    """
    Message every guardian on record. Returns how many were sent.

    Goes through the same delivery path as every other alert, so an SMS that
    fails is recorded as failed rather than assumed delivered — the whole point
    of replacing a tickbox.
    """
    from products.cyed.notifications.delivery import deliver
    from products.cyed.notifications.models import Notification

    student = visit.student
    if outcome == "emergency":
        subject = f"Urgent: {student.first_name} needs medical attention"
        body = (
            f"{student.first_name} is unwell at school and emergency services have been "
            f"called. Please contact the school office immediately."
        )
    else:
        subject = f"{student.first_name} is unwell and needs collecting"
        body = (
            f"{student.first_name} is in the sick bay and needs to be collected. "
            f"Please contact the school office."
        )

    # SMS where we have a number, because this is the message that must not
    # wait for someone to open an app.
    sent = 0
    for guardian in student.guardians.all():
        note = Notification.objects.create(
            tenant_id=visit.tenant_id,
            student=student,
            recipient_kind="guardian",
            recipient_name=f"{guardian.first_name} {guardian.last_name}".strip(),
            recipient_email=guardian.email,
            recipient_phone=guardian.phone,
            channel="sms" if guardian.phone else "in_app",
            category="wellbeing",
            subject=subject,
            body=body,
            related_model="cyed_health.SickBayVisit",
            related_id=str(visit.id),
            status="queued",
        )
        deliver(note)
        sent += 1
    return sent


def sick_bay_day(tenant_id, *, day=None):
    """Every visit for a day — the log a school produces when asked."""
    from products.cyed.health.models import SickBayVisit

    day = day or timezone.localdate()
    visits = SickBayVisit.objects.filter(
        tenant_id=tenant_id, arrived_at__date=day
    ).select_related("student", "seen_by").order_by("arrived_at")

    rows = []
    for visit in visits:
        rows.append({
            "visit": str(visit.id),
            "student": str(visit.student_id),
            "name": f"{visit.student.first_name} {visit.student.last_name}".strip(),
            "arrived_at": visit.arrived_at,
            "departed_at": visit.departed_at,
            "minutes_present": visit.minutes_present(),
            "complaint": visit.complaint,
            "treatment": visit.treatment,
            "outcome": visit.outcome,
            "collected_by": visit.collected_by,
            "guardians_notified": visit.guardians_notified,
            "seen_by": (
                f"{visit.seen_by.first_name} {visit.seen_by.last_name}".strip()
                if visit.seen_by_id else ""
            ),
        })
    counts = {}
    for row in rows:
        counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
    return {"date": day.isoformat(), "count": len(rows), "by_outcome": counts, "results": rows}


def action_plan_card(plan) -> dict:
    """
    One plan, shaped for reading in an emergency.

    Ordered the way it gets used: who, what they react to, what to do, where
    the medication is. Nothing above the steps that a teacher has to scroll
    past while a child is having a reaction.
    """
    student = plan.student
    return {
        "plan": str(plan.id),
        "student": str(student.id),
        "name": f"{student.first_name} {student.last_name}".strip(),
        "year_level": student.year_level,
        "plan_type": plan.plan_type,
        "plan_type_display": plan.get_plan_type_display(),
        "severity": plan.severity,
        "triggers": plan.triggers,
        "emergency_steps": plan.emergency_steps,
        "medication": plan.medication,
        "medication_location": plan.medication_location,
        "status": plan.status(),
        "review_due": plan.review_due.isoformat() if plan.review_due else None,
    }


def critical_plans(tenant_id, *, student_ids=None, campus_id=None):
    """
    Every current life-threatening plan, for a cohort or a whole campus.

    Used by the excursion roll and the emergency roll. Expired plans are
    included with their status rather than filtered out: a lapsed anaphylaxis
    plan is the single most important thing for a supervising teacher to know
    about, and hiding it because the paperwork is out of date would be the
    worst possible reading of "current".
    """
    plans = ActionPlan.objects.filter(
        tenant_id=tenant_id, is_active=True, plan_type__in=ActionPlan.CRITICAL_TYPES
    ).select_related("student")
    if student_ids is not None:
        plans = plans.filter(student_id__in=student_ids)
    if campus_id:
        plans = plans.filter(student__campus_id=campus_id)

    rows = [action_plan_card(p) for p in plans]
    # Critical first, then expired plans ahead of current ones — both are
    # things a supervisor must see before the routine cases.
    severity_order = {"critical": 0, "high": 1, "moderate": 2}
    status_order = {"expired": 0, "due_for_review": 1}
    rows.sort(key=lambda r: (
        severity_order.get(r["severity"], 9),
        status_order.get(r["status"], 5),
        r["name"],
    ))
    return rows


def plans_needing_review(tenant_id, *, as_at=None):
    """Expired or soon-to-expire plans — the health office's chase list."""
    as_at = as_at or timezone.localdate()
    rows = []
    for plan in ActionPlan.objects.filter(
        tenant_id=tenant_id, is_active=True, student__enrolment_status="enrolled"
    ).select_related("student"):
        status = plan.status(as_at)
        if status in ("current",):
            continue
        rows.append({
            **action_plan_card(plan),
            "days_until_review": (
                (plan.review_due - as_at).days if plan.review_due else None
            ),
        })
    order = {"expired": 0, "no_review_date": 1, "due_for_review": 2}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["name"]))
    return rows


class MedicationError(Exception):
    """A dose was refused on safety grounds (→ HTTP 400/409)."""


# ── immunisation ─────────────────────────────────────────────────────────────
def immunisation_gaps(tenant_id, *, campus_id=None, year_level=None):
    """
    Enrolled students whose immunisation evidence does not satisfy enrolment.

    Includes students with *no* record at all — the common real case, and the
    one a query over `ImmunisationRecord` alone would silently miss. A child
    nobody has asked about looks identical to a compliant one if you only read
    the rows that exist.
    """
    students = Student.objects.filter(
        tenant_id=tenant_id, enrolment_status="enrolled"
    ).select_related("immunisation")
    if campus_id:
        students = students.filter(campus_id=campus_id)
    if year_level:
        students = students.filter(year_level=year_level)

    rows = []
    for student in students:
        record = getattr(student, "immunisation", None)
        if record is not None and record.is_acceptable_at_enrolment():
            continue
        rows.append({
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "status": record.status if record else "no_record",
            "verified_on": record.verified_on.isoformat() if record and record.verified_on else None,
            "reason": (
                "No immunisation record has been created for this student."
                if record is None
                else "Status is not acceptable at enrolment."
                if record.status not in ImmunisationRecord.ACCEPTABLE_AT_ENROLMENT
                else "Statement has not been sighted and verified."
            ),
        })
    rows.sort(key=lambda r: (r["year_level"] or 0, r["name"]))
    return rows


def outbreak_exclusion_list(tenant_id, disease, *, campus_id=None):
    """
    Who must be kept away during an outbreak of `disease`.

    A medical exemption does not appear as protection here. An exempt child is
    exactly the one an exclusion directive exists to protect, so treating
    "lawfully enrolled" as "safe during an outbreak" would invert the purpose
    of the register.
    """
    students = Student.objects.filter(
        tenant_id=tenant_id, enrolment_status="enrolled"
    ).select_related("immunisation").prefetch_related("immunisation__doses")
    if campus_id:
        students = students.filter(campus_id=campus_id)

    excluded = []
    for student in students:
        record = getattr(student, "immunisation", None)
        if record is not None and record.protected_against(disease):
            continue
        excluded.append({
            "student": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "status": record.status if record else "no_record",
            "basis": (
                "No immunisation record" if record is None
                else "No recorded dose protecting against this disease"
            ),
        })
    excluded.sort(key=lambda r: (r["year_level"] or 0, r["name"]))
    return {
        "disease": disease,
        "count": len(excluded),
        "students": excluded,
    }


# ── medication ───────────────────────────────────────────────────────────────
def check_dose(authority, *, when=None, outcome="given"):
    """
    Verify a dose is permitted. Returns a verdict rather than raising, so the
    caller can decide whether an override applies.

    A refusal or an omission is always allowed to be recorded: the whole point
    of logging "not given" is that it happened outside the plan, and blocking
    the record would destroy the evidence of exactly the event that matters.
    """
    when = when or timezone.now()
    day = timezone.localtime(when).date()

    if outcome != "given":
        return {"permitted": True, "reason": "", "checks": ["non-administration outcome"]}

    if not authority.is_current(day):
        if not authority.is_active:
            reason = "This medication authority has been withdrawn."
        elif authority.start_date and day < authority.start_date:
            reason = f"This authority does not start until {authority.start_date}."
        else:
            reason = f"This authority expired on {authority.end_date}."
        return {"permitted": False, "reason": reason, "checks": ["authority currency"]}

    given_today = authority.doses_given_on(day)
    if authority.max_doses_per_day and given_today >= authority.max_doses_per_day:
        return {
            "permitted": False,
            "reason": (
                f"{given_today} dose(s) already given today; the authority permits "
                f"{authority.max_doses_per_day} per day."
            ),
            "checks": ["daily maximum"],
        }

    min_gap = Decimal(authority.min_hours_between_doses or 0)
    if min_gap > 0:
        previous = authority.last_dose_before(when)
        if previous is not None:
            elapsed = when - previous.administered_at
            required = timedelta(hours=float(min_gap))
            if elapsed < required:
                remaining = required - elapsed
                minutes = int(remaining.total_seconds() // 60)
                return {
                    "permitted": False,
                    "reason": (
                        f"Last dose was at {timezone.localtime(previous.administered_at):%H:%M}; "
                        f"{min_gap} hours must elapse between doses ({minutes} min remaining)."
                    ),
                    "checks": ["minimum interval"],
                }

    return {"permitted": True, "reason": "", "checks": ["authority currency", "daily maximum", "minimum interval"]}


def administer(
    *, authority, administered_by, dose_given="", when=None, outcome="given",
    witnessed_by=None, self_administered=False, notes="",
    override_reason="", override_by="",
):
    """
    Record a dose, refusing the ones that should not happen.

    `administered_by` is mandatory and is a Staff record, not a name: a dose
    with nobody accountable for it is not a duty-of-care record. Overriding a
    limit is possible — a prescriber can authorise an extra dose by phone —
    but it must leave a reason behind, or it is indistinguishable from a bug.
    """
    when = when or timezone.now()

    if administered_by is None:
        raise MedicationError(
            "Record the staff member who administered the dose — an unattributed "
            "dose is not a duty-of-care record."
        )
    if self_administered and not authority.self_administer_permitted:
        raise MedicationError(
            f"The authority for {authority.medication_name} does not permit "
            f"self-administration."
        )

    verdict = check_dose(authority, when=when, outcome=outcome)
    if not verdict["permitted"]:
        if not override_reason:
            raise MedicationError(verdict["reason"])

    return MedicationAdministration.objects.create(
        tenant_id=authority.tenant_id,
        authority=authority,
        student_id=authority.student_id,
        administered_at=when,
        administered_on=timezone.localtime(when).date(),
        dose_given=dose_given or authority.dose,
        outcome=outcome,
        administered_by=administered_by,
        witnessed_by=witnessed_by,
        self_administered=self_administered,
        notes=notes,
        limit_override_by=override_by if not verdict["permitted"] else "",
        limit_override_reason=(override_reason[:255] if not verdict["permitted"] else ""),
    )


def medication_due_today(tenant_id, *, day=None, campus_id=None):
    """
    The first-aid room's worklist: current authorities and how many doses have
    already gone out today.

    Deliberately shows what has been given rather than a schedule of times —
    school medication is mostly conditional ("before sport", "if wheezing"),
    so the useful question is "has this child had theirs?", not "is it 11am?".
    """
    day = day or timezone.localdate()
    authorities = MedicationAuthority.objects.filter(
        tenant_id=tenant_id, is_active=True
    ).select_related("student")
    if campus_id:
        authorities = authorities.filter(student__campus_id=campus_id)

    rows = []
    for authority in authorities:
        if not authority.is_current(day):
            continue
        given = authority.doses_given_on(day)
        rows.append({
            "authority": str(authority.id),
            "student": str(authority.student_id),
            "name": f"{authority.student.first_name} {authority.student.last_name}".strip(),
            "medication": authority.medication_name,
            "dose": authority.dose,
            "route": authority.route,
            "max_doses_per_day": authority.max_doses_per_day,
            "given_today": given,
            "remaining_today": max(0, (authority.max_doses_per_day or 0) - given),
            "self_administer_permitted": authority.self_administer_permitted,
        })
    rows.sort(key=lambda r: r["name"])
    return rows
