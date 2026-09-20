import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone

from products.cyed.admissions.models import Application
from products.cyed.governance.models import AuditEvent
from products.cyed.governance.retention import (
    sweep_applications,
    sweep_students,
    sweep_visitors,
)
from products.cyed.sis.models import Student
from products.cyed.visitors.models import Visitor


@pytest.mark.django_db
def test_students_dry_run_matches_but_does_not_act(tenant_id):
    old_exit = date.today().replace(year=date.today().year - 8)
    Student.objects.create(
        tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=10,
        enrolment_status="graduated", exit_date=old_exit,
    )
    result = sweep_students(tenant_id, apply=False)
    assert result.matched == 1
    assert result.acted == 0
    s = Student.objects.get(tenant_id=tenant_id)
    assert s.first_name == "Ava"  # untouched


@pytest.mark.django_db
def test_students_apply_deidentifies_and_logs(tenant_id):
    old_exit = date.today().replace(year=date.today().year - 8)
    student = Student.objects.create(
        tenant_id=tenant_id, first_name="Ben", last_name="Ng", year_level=11,
        enrolment_status="withdrawn", exit_date=old_exit,
    )
    result = sweep_students(tenant_id, apply=True)
    assert result.acted == 1
    student.refresh_from_db()
    assert student.first_name == "De-identified"
    assert student.date_of_birth is None
    assert AuditEvent.objects.filter(
        tenant_id=tenant_id, model_label="cyed_sis.Student", object_id=str(student.id),
        actor="system:retention_sweep",
    ).exists()


@pytest.mark.django_db
def test_students_recently_exited_is_untouched(tenant_id):
    Student.objects.create(
        tenant_id=tenant_id, first_name="Cy", last_name="Tran", year_level=12,
        enrolment_status="graduated", exit_date=date.today() - timedelta(days=30),
    )
    result = sweep_students(tenant_id, apply=True)
    assert result.matched == 0


@pytest.mark.django_db
def test_students_still_enrolled_is_never_touched(tenant_id):
    Student.objects.create(
        tenant_id=tenant_id, first_name="Dee", last_name="Osei", year_level=8,
        enrolment_status="enrolled", exit_date=None,
    )
    result = sweep_students(tenant_id, apply=True)
    assert result.matched == 0


@pytest.mark.django_db
def test_students_already_deidentified_is_skipped(tenant_id):
    old_exit = date.today().replace(year=date.today().year - 8)
    Student.objects.create(
        tenant_id=tenant_id, first_name="De-identified", last_name="Student abc12345",
        year_level=10, enrolment_status="withdrawn", exit_date=old_exit,
    )
    result = sweep_students(tenant_id, apply=True)
    assert result.matched == 0


@pytest.mark.django_db
def test_visitors_apply_purges_and_logs(tenant_id):
    old = Visitor.objects.create(tenant_id=tenant_id, full_name="Old Visitor")
    Visitor.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=500))
    recent = Visitor.objects.create(tenant_id=tenant_id, full_name="Recent Visitor")

    result = sweep_visitors(tenant_id, apply=True)
    assert result.matched == 1
    assert result.acted == 1
    assert not Visitor.objects.filter(pk=old.pk).exists()
    assert Visitor.objects.filter(pk=recent.pk).exists()
    assert AuditEvent.objects.filter(
        tenant_id=tenant_id, model_label="cyed_visitors.Visitor", actor="system:retention_sweep",
    ).exists()


@pytest.mark.django_db
def test_applications_only_terminal_states_purged(tenant_id):
    old = timezone.now() - timedelta(days=800)
    declined = Application.objects.create(
        tenant_id=tenant_id, applicant_first_name="A", applicant_last_name="B", status="declined",
    )
    Application.objects.filter(pk=declined.pk).update(created_at=old)
    still_open = Application.objects.create(
        tenant_id=tenant_id, applicant_first_name="C", applicant_last_name="D", status="waitlisted",
    )
    Application.objects.filter(pk=still_open.pk).update(created_at=old)

    result = sweep_applications(tenant_id, apply=True)
    assert result.matched == 1
    assert not Application.objects.filter(pk=declined.pk).exists()
    assert Application.objects.filter(pk=still_open.pk).exists()


@pytest.mark.django_db
def test_sweep_is_tenant_scoped(tenant_id):
    other_tenant = uuid.uuid4()
    old_exit = date.today().replace(year=date.today().year - 8)
    Student.objects.create(
        tenant_id=other_tenant, first_name="Eli", last_name="Wong", year_level=10,
        enrolment_status="graduated", exit_date=old_exit,
    )
    result = sweep_students(tenant_id, apply=True)
    assert result.matched == 0
    assert Student.objects.get(tenant_id=other_tenant).first_name == "Eli"
