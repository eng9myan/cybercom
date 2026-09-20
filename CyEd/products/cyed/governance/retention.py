"""
Automated data retention / disposal — the "⚙️ Cron/management command to add"
item ST4S_COMPLIANCE_MAP.md and the procurement audit both flagged as
outstanding. Reused nowhere else, deliberately: this is the ONE place a
retention window is decided, so a school's DPO can point to one file.

Windows below are defaults, not a legal claim about any specific
jurisdiction's record-keeping law — a school must confirm its own statutory
retention period (state education department policy, APP 11.2) and adjust
`RETENTION_POLICIES` accordingly. What's real is the mechanism: dry-run by
default, every action logged to AuditEvent, nothing is silently deleted.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

RETENTION_POLICIES = {
    # Long-departed students are de-identified (not deleted) so anonymised
    # statistics survive — same irreversible operation StudentViewSet.deidentify
    # already exposes for a manual, single-record case; this just finds the
    # rows and applies it in bulk.
    "students": {"years": 7},
    # Visitor sign-in logs are an operational/security record, not a
    # long-term one — hard-deleted past the window.
    "visitors": {"days": 365},
    # An application that never became an enrolment has no ongoing reason
    # to keep PII once its own outcome is old. Only terminal, unsuccessful
    # states are touched — an open/waitlisted application is never purged.
    "applications": {"years": 2},
}


@dataclass
class RetentionResult:
    category: str
    matched: int
    acted: int
    sample_ids: list


def _cutoff(*, years: int = 0, days: int = 0):
    now = timezone.localdate()
    if years:
        try:
            return now.replace(year=now.year - years)
        except ValueError:
            # Feb 29 on a non-leap cutoff year — fall back a day, not forward
            # into a date the loop would then never reach.
            return now.replace(month=2, day=28, year=now.year - years)
    return now - timedelta(days=days)


def sweep_students(tenant_id=None, *, apply: bool = False) -> RetentionResult:
    from products.cyed.governance.models import AuditEvent
    from products.cyed.sis.models import Student

    cutoff = _cutoff(**RETENTION_POLICIES["students"])
    qs = Student.objects.filter(
        enrolment_status__in=["graduated", "withdrawn"],
        exit_date__isnull=False,
        exit_date__lt=cutoff,
    ).exclude(first_name="De-identified")
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    matched = list(qs)
    acted = 0
    for student in matched:
        if apply:
            student.first_name = "De-identified"
            student.last_name = f"Student {str(student.id)[:8]}"
            student.email = ""
            student.student_number = ""
            student.date_of_birth = None
            student.save()
            student.guardians.clear()
            AuditEvent.objects.create(
                tenant_id=student.tenant_id, actor="system:retention_sweep",
                action="update", model_label="cyed_sis.Student", object_id=str(student.id),
                summary=f"Auto de-identified — exited {cutoff.isoformat()} retention window.",
            )
            acted += 1

    return RetentionResult("students", len(matched), acted, [str(s.id) for s in matched[:20]])


def sweep_visitors(tenant_id=None, *, apply: bool = False) -> RetentionResult:
    from products.cyed.governance.models import AuditEvent
    from products.cyed.visitors.models import Visitor

    cutoff = _cutoff(**RETENTION_POLICIES["visitors"])
    qs = Visitor.objects.filter(created_at__date__lt=cutoff)
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    matched = list(qs.values_list("id", "tenant_id"))
    acted = 0
    if apply and matched:
        for visitor_id, visitor_tenant_id in matched:
            AuditEvent.objects.create(
                tenant_id=visitor_tenant_id, actor="system:retention_sweep",
                action="delete", model_label="cyed_visitors.Visitor", object_id=str(visitor_id),
                summary=f"Auto-purged — signed in before {cutoff.isoformat()}.",
            )
        acted = qs.delete()[0]

    return RetentionResult("visitors", len(matched), acted, [str(i) for i, _ in matched[:20]])


def sweep_applications(tenant_id=None, *, apply: bool = False) -> RetentionResult:
    from products.cyed.admissions.models import Application
    from products.cyed.governance.models import AuditEvent

    cutoff = _cutoff(**RETENTION_POLICIES["applications"])
    qs = Application.objects.filter(
        status__in=["declined", "withdrawn"], created_at__date__lt=cutoff,
    )
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    matched = list(qs.values_list("id", "tenant_id"))
    acted = 0
    if apply and matched:
        for app_id, app_tenant_id in matched:
            AuditEvent.objects.create(
                tenant_id=app_tenant_id, actor="system:retention_sweep",
                action="delete", model_label="cyed_admissions.Application", object_id=str(app_id),
                summary=f"Auto-purged — declined/withdrawn before {cutoff.isoformat()}.",
            )
        acted = qs.delete()[0]

    return RetentionResult("applications", len(matched), acted, [str(i) for i, _ in matched[:20]])


def run_all(tenant_id=None, *, apply: bool = False) -> list:
    return [
        sweep_students(tenant_id, apply=apply),
        sweep_visitors(tenant_id, apply=apply),
        sweep_applications(tenant_id, apply=apply),
    ]
