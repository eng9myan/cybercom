"""
Daily notices.

The tests are mostly about addressing and expiry — the two things that decide
whether a noticeboard gets read or scrolled past.
"""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.school.models import Notice
from products.cyed.sis.models import Guardian, Student

TODAY = timezone.localdate()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def office(client_for):
    return client_for(["tenant_admin"], "office@cyed.edu.au")


@pytest.fixture
def year9_student(client_for, tenant_id):
    Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=9,
        enrolment_status="enrolled", email="mia@student.cyed.edu.au",
    )
    return client_for(["student"], "mia@student.cyed.edu.au")


@pytest.fixture
def year9_parent(client_for, tenant_id):
    student = Student.objects.create(
        tenant_id=tenant_id, first_name="Ken", last_name="Ito", year_level=9,
        enrolment_status="enrolled",
    )
    Guardian.objects.create(
        tenant_id=tenant_id, first_name="Yui", last_name="Ito", email="yui@example.com"
    ).students.add(student)
    return client_for(["parent"], "yui@example.com")


def _notice(tenant_id, title="No hats at lunch", **extra):
    body = {
        "tenant_id": tenant_id,
        "title": title,
        "body": "Please remind students.",
        "audience": "all",
        "starts_on": TODAY,
        "is_published": True,
    }
    body.update(extra)
    return Notice.objects.create(**body)


# ── the window ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_current_notice_is_on_the_board(office, tenant_id):
    _notice(tenant_id)
    resp = office.get("/api/v1/school/notices/today/")
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_a_finished_notice_comes_down(office, tenant_id):
    """A board that only grows is one nobody reads by week three."""
    _notice(tenant_id, starts_on=TODAY - timedelta(days=10), ends_on=TODAY - timedelta(days=1))
    assert office.get("/api/v1/school/notices/today/").data["count"] == 0


@pytest.mark.django_db
def test_a_future_notice_is_not_shown_yet(office, tenant_id):
    _notice(tenant_id, starts_on=TODAY + timedelta(days=3))
    assert office.get("/api/v1/school/notices/today/").data["count"] == 0


@pytest.mark.django_db
def test_a_notice_with_no_end_date_keeps_running(office, tenant_id):
    _notice(tenant_id, ends_on=None)
    assert office.get("/api/v1/school/notices/today/").data["count"] == 1


@pytest.mark.django_db
def test_an_unpublished_notice_is_invisible_to_families(year9_parent, tenant_id):
    _notice(tenant_id, is_published=False)
    assert year9_parent.get("/api/v1/school/notices/today/").data["count"] == 0


@pytest.mark.django_db
def test_ending_before_starting_is_refused(office):
    resp = office.post("/api/v1/school/notices/", {
        "title": "Backwards", "body": "x",
        "starts_on": TODAY.isoformat(),
        "ends_on": (TODAY - timedelta(days=1)).isoformat(),
    }, format="json")
    assert resp.status_code == 400
    assert "cannot come down before" in str(resp.data)


# ── addressing ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_students_board_excludes_staff_only_notices(year9_student, tenant_id):
    _notice(tenant_id, "Staff briefing 8am", audience="staff")
    _notice(tenant_id, "Assembly at 9", audience="students")

    resp = year9_student.get("/api/v1/school/notices/today/")
    assert [n["title"] for n in resp.data["results"]] == ["Assembly at 9"]


@pytest.mark.django_db
def test_everyone_sees_an_all_audience_notice(year9_parent, tenant_id):
    _notice(tenant_id, "Pupil-free day Friday", audience="all")
    assert year9_parent.get("/api/v1/school/notices/today/").data["count"] == 1


@pytest.mark.django_db
def test_a_year_specific_notice_does_not_fill_another_years_screen(
    year9_student, client_for, tenant_id
):
    """A Year 10 excursion notice on a Year 9 screen is how boards get ignored."""
    _notice(tenant_id, "Year 10 excursion money due", year_levels="10")
    assert year9_student.get("/api/v1/school/notices/today/").data["count"] == 0

    _notice(tenant_id, "Year 9 camp forms", year_levels="9,10")
    resp = year9_student.get("/api/v1/school/notices/today/")
    assert [n["title"] for n in resp.data["results"]] == ["Year 9 camp forms"]


@pytest.mark.django_db
def test_a_parent_sees_notices_for_any_of_their_children(client_for, tenant_id):
    """A parent with children in 7 and 10 needs both, not one chosen arbitrarily."""
    parent = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran", email="hoa@example.com"
    )
    for year in (7, 10):
        student = Student.objects.create(
            tenant_id=tenant_id, first_name=f"Y{year}", last_name="Tran",
            year_level=year, enrolment_status="enrolled",
        )
        parent.students.add(student)

    _notice(tenant_id, "Year 7 swimming", year_levels="7")
    _notice(tenant_id, "Year 10 subject selection", year_levels="10")
    _notice(tenant_id, "Year 12 formal", year_levels="12")

    resp = client_for(["parent"], "hoa@example.com").get("/api/v1/school/notices/today/")
    titles = {n["title"] for n in resp.data["results"]}
    assert titles == {"Year 7 swimming", "Year 10 subject selection"}


@pytest.mark.django_db
def test_staff_see_every_year_level(office, tenant_id):
    _notice(tenant_id, "Year 7 swimming", year_levels="7")
    _notice(tenant_id, "Year 12 formal", year_levels="12")
    assert office.get("/api/v1/school/notices/today/").data["count"] == 2


# ── ordering and authorship ──────────────────────────────────────────────────
@pytest.mark.django_db
def test_urgent_notices_come_first(office, tenant_id):
    _notice(tenant_id, "Normal thing", priority="normal")
    _notice(tenant_id, "Bus 12 cancelled", priority="urgent")
    _notice(tenant_id, "Reminder", priority="important")

    titles = [n["title"] for n in office.get("/api/v1/school/notices/today/").data["results"]]
    assert titles[0] == "Bus 12 cancelled"
    assert titles[1] == "Reminder"


@pytest.mark.django_db
def test_the_author_is_stamped_from_the_token(office):
    """A notice attributed to someone who did not write it is worse than none."""
    resp = office.post("/api/v1/school/notices/", {
        "title": "Test", "body": "x", "posted_by": "someone.else@example.com",
    }, format="json")
    assert resp.status_code == 201
    assert resp.data["posted_by"] == "office@cyed.edu.au"


@pytest.mark.django_db
def test_families_cannot_post_notices(year9_parent):
    resp = year9_parent.post("/api/v1/school/notices/", {"title": "Hi", "body": "x"},
                             format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_a_bad_year_level_is_refused(office):
    resp = office.post("/api/v1/school/notices/", {
        "title": "Typo", "body": "x", "year_levels": "nine",
    }, format="json")
    assert resp.status_code == 400
    assert "not a year level" in str(resp.data)
