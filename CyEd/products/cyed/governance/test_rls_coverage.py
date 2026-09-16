"""
Row-Level Security coverage.

RLS lives in migrations that nobody edits when a new model lands, and the
policies are a no-op on SQLite — so a table added without a policy looks
perfectly fine in the test suite and is unprotected in production. That is how
the gap this test exists to catch was introduced: eighteen tables holding
student and staff personal data were created after the original RLS migration
and none of them were covered.

This test does not exercise RLS (that needs PostgreSQL). It checks the far
cheaper property that catches the realistic mistake: every tenant-scoped model
holding personal data is named in one of the RLS migrations.
"""

import pytest
from django.apps import apps as django_apps

pytestmark = pytest.mark.django_db


def _covered_tables():
    # Discovered from the migrations, not listed here — see governance/rls.py.
    from products.cyed.governance.rls import covered_tables

    return covered_tables()


# Models whose rows are about a named person, or are the household/finance
# records attached to one. A leak across tenants here is a privacy incident,
# not an inconvenience.
SENSITIVE_MODELS = {
    "cyed_sis.Student",
    "cyed_sis.Guardian",
    "cyed_sis.TransferCertificate",
    "cyed_sis.CampusTransfer",
    "cyed_health.HealthRecord",
    "cyed_health.MedicalIncident",
    "cyed_health.ImmunisationRecord",
    "cyed_health.ImmunisationDose",
    "cyed_health.MedicationAuthority",
    "cyed_health.MedicationAdministration",
    "cyed_wellbeing.WellbeingNote",
    "cyed_wellbeing.WellbeingCheckIn",
    "cyed_wellbeing.BehaviourIncident",
    "cyed_wellbeing.LearnerProfile",
    "cyed_messaging.MessageThread",
    "cyed_messaging.Message",
    "cyed_messaging.ThreadParticipant",
    "cyed_exams.ExamCandidate",
    "cyed_billing.StudentBill",
    "cyed_billing.Installment",
    "cyed_billing.CreditNote",
    "cyed_billing.DunningCase",
    "cyed_attendance.AttendanceMark",
    "cyed_attendance.AbsenceExplanation",
    "cyed_attendance.EmergencyDrill",
    "cyed_attendance.EmergencyRollEntry",
    "cyed_health.ActionPlan",
    "cyed_hr.StaffClearance",
    "cyed_library.Loan",
    "cyed_sif.SifRefId",
    "cyed_substitution.ReliefTeacher",
    "cyed_substitution.ReliefBooking",
    "cyed_meetings.InterviewBooking",
    "cyed_wellbeing.SupportPlan",
    "cyed_wellbeing.SupportAdjustment",
    "cyed_wellbeing.SupportGoal",
    "cyed_wellbeing.SupportPlanReview",
    "cyed_health.SickBayVisit",
    "cyed_gradebook.RubricMark",
    "cyed_notifications.PushDevice",
    "cyed_events.EventParticipation",
}


def test_rls_covers_every_sensitive_table():
    """
    Fails when a model holding personal data has no RLS policy.

    If this fails because you added a legitimately new sensitive model: add its
    table to a new RLS migration and its label here. Do not delete the entry.
    """
    covered = _covered_tables()
    missing = []
    for label in sorted(SENSITIVE_MODELS):
        app_label, model_name = label.split(".")
        model = django_apps.get_model(app_label, model_name)
        table = model._meta.db_table
        if table not in covered:
            missing.append(f"{label} ({table})")

    assert not missing, (
        "These tables hold personal data but have no Row-Level Security policy, "
        "so a logic bug or raw query could read across tenants:\n  "
        + "\n  ".join(missing)
    )


def test_every_rls_table_actually_exists():
    """
    A policy naming a table that was renamed or dropped would fail the migration
    on deploy — after the release has already started.
    """
    real_tables = {m._meta.db_table for m in django_apps.get_models()}
    named = _covered_tables()
    unknown = sorted(named - real_tables)
    assert not unknown, f"RLS migrations name tables that no model defines: {unknown}"


def test_rls_tables_all_carry_a_tenant_id():
    """The policy compares `tenant_id`; a table without one would error at runtime."""
    by_table = {m._meta.db_table: m for m in django_apps.get_models()}
    offenders = []
    for table in sorted(_covered_tables()):
        model = by_table.get(table)
        if model is None:
            continue
        if not any(f.name == "tenant_id" for f in model._meta.fields):
            offenders.append(table)
    assert not offenders, f"RLS policy references tenant_id on tables without it: {offenders}"
