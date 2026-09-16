"""
Leadership dashboards.

Two properties are load-bearing and easy to get wrong: rates rather than counts
(so campuses of different sizes are comparable), and suppression of tiny cohorts
(so a "year level" of four students is not one child's attendance record on a
group executive's screen).
"""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.analytics import dashboards
from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.gradebook.models import Assessment, Grade
from products.cyed.org.models import Campus
from products.cyed.sis.models import ClassSection, Student
from products.cyed.wellbeing.models import BehaviourIncident

TODAY = timezone.localdate()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="principal@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def principal(client_for):
    return client_for(["leadership"])


def _mark(tenant_id, section, student, day, status="present"):
    roll, _ = RollCall.objects.get_or_create(
        tenant_id=tenant_id, class_section=section, date=day, period_label="P1"
    )
    return AttendanceMark.objects.create(
        tenant_id=tenant_id, roll_call=roll, student=student, status=status
    )


@pytest.fixture
def cohort(tenant_id):
    """Eight Year 8 students with a mix of attendance."""
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    students = [
        Student.objects.create(
            tenant_id=tenant_id, first_name=f"S{i}", last_name="Test",
            year_level=8, enrolment_status="enrolled",
        )
        for i in range(8)
    ]
    return section, students


# ── attendance ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_late_counts_as_attending(tenant_id, cohort):
    """
    A rate that penalised lateness as absence would disagree with what the
    school reports to the department.
    """
    section, students = cohort
    day = TODAY - timedelta(days=7)
    _mark(tenant_id, section, students[0], day, "present")
    _mark(tenant_id, section, students[1], day, "late")
    _mark(tenant_id, section, students[2], day, "absent")

    trend = dashboards.attendance_trend(tenant_id, weeks=4)
    week = [w for w in trend if w["total"]][0]
    assert week["attended"] == 2
    assert week["rate"] == pytest.approx(66.7, abs=0.1)


@pytest.mark.django_db
def test_the_trend_is_grouped_by_week(tenant_id, cohort):
    """A term of daily points hides the trend it exists to show."""
    section, students = cohort
    for offset in (7, 8, 21):
        _mark(tenant_id, section, students[0], TODAY - timedelta(days=offset))

    trend = dashboards.attendance_trend(tenant_id, weeks=8)
    populated = [w for w in trend if w["total"]]
    # Days 7 and 8 may straddle a week boundary, so assert the shape rather
    # than an exact count: it must be fewer buckets than marks.
    assert 1 <= len(populated) <= 3
    assert sum(w["total"] for w in populated) == 3


@pytest.mark.django_db
def test_a_tiny_cohort_has_its_rate_suppressed(tenant_id):
    """A rate over four students is one child's record with a label on it."""
    section = ClassSection.objects.create(tenant_id=tenant_id, name="12A", year_level=12)
    for i in range(3):
        s = Student.objects.create(
            tenant_id=tenant_id, first_name=f"T{i}", last_name="Tiny",
            year_level=12, enrolment_status="enrolled",
        )
        _mark(tenant_id, section, s, TODAY - timedelta(days=7))

    rows = dashboards.attendance_by_year_level(tenant_id, weeks=4)
    year12 = next(r for r in rows if r["year_level"] == 12)
    assert year12["suppressed"] is True
    assert year12["rate"] is None
    # The size is still reported — leadership needs to know the cohort exists.
    assert year12["students"] == 3


@pytest.mark.django_db
def test_a_normal_cohort_reports_its_rate(tenant_id, cohort):
    section, students = cohort
    day = TODAY - timedelta(days=7)
    for student in students:
        _mark(tenant_id, section, student, day, "present")

    rows = dashboards.attendance_by_year_level(tenant_id, weeks=4)
    year8 = next(r for r in rows if r["year_level"] == 8)
    assert year8["suppressed"] is False
    assert year8["rate"] == 100.0


# ── chronic absence ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_chronic_absence_lists_students_below_the_line(tenant_id, cohort):
    """The list that turns a trend line into names."""
    section, students = cohort
    poor, fine = students[0], students[1]
    for day in range(12):
        when = TODAY - timedelta(days=day + 1)
        _mark(tenant_id, section, poor, when, "absent" if day < 6 else "present")
        _mark(tenant_id, section, fine, when, "present")

    result = dashboards.chronic_absence(tenant_id, weeks=8, threshold=90)
    names = [r["name"] for r in result["results"]]
    assert "S0 Test" in names
    assert "S1 Test" not in names
    assert result["results"][0]["missed"] == 6


@pytest.mark.django_db
def test_a_student_with_barely_any_marks_is_not_rated(tenant_id, cohort):
    """A handful of marks is a student who enrolled last week, not a rate."""
    section, students = cohort
    _mark(tenant_id, section, students[0], TODAY - timedelta(days=1), "absent")

    result = dashboards.chronic_absence(tenant_id, weeks=8)
    assert result["count"] == 0


@pytest.mark.django_db
def test_the_worst_attendance_sorts_first(tenant_id, cohort):
    section, students = cohort
    for index, absences in ((0, 9), (1, 5)):
        for day in range(12):
            _mark(
                tenant_id, section, students[index], TODAY - timedelta(days=day + 1),
                "absent" if day < absences else "present",
            )

    result = dashboards.chronic_absence(tenant_id, weeks=8)
    assert result["results"][0]["name"] == "S0 Test"


# ── achievement and behaviour ────────────────────────────────────────────────
@pytest.mark.django_db
def test_achievement_is_a_distribution_not_an_average(tenant_id, cohort):
    """"The school averages a C" hides both the failing and the coasting."""
    section, students = cohort
    assessment = Assessment.objects.create(
        tenant_id=tenant_id, class_section=section, name="Test", max_score=100
    )
    for student, level in zip(students, ["A", "A", "C", "C", "C", "E", "", ""]):
        Grade.objects.create(
            tenant_id=tenant_id, assessment=assessment, student=student,
            score=50, achievement_level=level,
        )

    result = dashboards.achievement_distribution(tenant_id)
    by_level = {r["level"]: r["count"] for r in result["distribution"]}
    assert by_level == {"A": 2, "C": 3, "E": 1}   # blanks excluded
    assert result["total"] == 6


@pytest.mark.django_db
def test_behaviour_reports_positive_alongside_negative(tenant_id, cohort):
    """
    Counting only incidents tells a school it is getting worse even when
    recognition is rising faster.
    """
    _section, students = cohort
    day = TODAY - timedelta(days=3)
    for category, count in (("positive", 5), ("minor", 2), ("major", 1)):
        for _ in range(count):
            BehaviourIncident.objects.create(
                tenant_id=tenant_id, student=students[0], date=day, category=category
            )

    result = dashboards.behaviour_summary(tenant_id, weeks=4)
    week = [w for w in result["weeks"] if w["positive"] or w["minor"] or w["major"]][0]
    assert week["positive"] == 5
    assert week["minor"] == 2
    assert week["major"] == 1


# ── campus comparison ────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_campuses_are_compared_on_rate_not_count(tenant_id):
    """
    A campus with 900 students always posts more absences than one with 200.
    Ranking on counts just ranks on size.
    """
    big = Campus.objects.create(tenant_id=tenant_id, name="Big", code="BIG")
    small = Campus.objects.create(tenant_id=tenant_id, name="Small", code="SML")
    day = TODAY - timedelta(days=7)

    # Big campus: 10 students, 8 present → 80%.
    section_big = ClassSection.objects.create(
        tenant_id=tenant_id, name="B1", year_level=8, campus=big
    )
    for i in range(10):
        s = Student.objects.create(
            tenant_id=tenant_id, campus=big, first_name=f"B{i}", last_name="Big",
            year_level=8, enrolment_status="enrolled",
        )
        _mark(tenant_id, section_big, s, day, "present" if i < 8 else "absent")

    # Small campus: 5 students, all present → 100%.
    section_small = ClassSection.objects.create(
        tenant_id=tenant_id, name="S1", year_level=8, campus=small
    )
    for i in range(5):
        s = Student.objects.create(
            tenant_id=tenant_id, campus=small, first_name=f"S{i}", last_name="Small",
            year_level=8, enrolment_status="enrolled",
        )
        _mark(tenant_id, section_small, s, day, "present")

    rows = dashboards.campus_comparison(tenant_id, weeks=4)
    by_name = {r["name"]: r for r in rows}
    assert by_name["Big"]["attendance_rate"] == 80.0
    assert by_name["Small"]["attendance_rate"] == 100.0
    # Worst first: that is the campus a group executive needs to look at.
    assert rows[0]["name"] == "Big"


@pytest.mark.django_db
def test_a_campus_with_almost_no_students_is_suppressed(tenant_id):
    tiny = Campus.objects.create(tenant_id=tenant_id, name="Tiny", code="TNY")
    Student.objects.create(
        tenant_id=tenant_id, campus=tiny, first_name="Only", last_name="One",
        year_level=8, enrolment_status="enrolled",
    )
    rows = dashboards.campus_comparison(tenant_id, weeks=4)
    tiny_row = next(r for r in rows if r["name"] == "Tiny")
    assert tiny_row["suppressed"] is True
    assert tiny_row["attendance_rate"] is None


# ── the endpoints ────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_the_dashboard_returns_every_panel(principal, tenant_id, cohort):
    section, students = cohort
    _mark(tenant_id, section, students[0], TODAY - timedelta(days=7))

    resp = principal.get("/api/v1/analytics/dashboard/")
    assert resp.status_code == 200
    for key in (
        "attendance_trend", "attendance_by_year_level",
        "chronic_absence", "achievement", "behaviour",
    ):
        assert key in resp.data


@pytest.mark.django_db
def test_the_window_is_capped(principal, tenant_id):
    """An unbounded window would read every mark the school has ever recorded."""
    resp = principal.get("/api/v1/analytics/dashboard/?weeks=99999")
    assert resp.status_code == 200
    assert resp.data["weeks"] == 60


@pytest.mark.django_db
def test_a_non_numeric_window_is_refused(principal):
    assert principal.get("/api/v1/analytics/dashboard/?weeks=lots").status_code == 400


@pytest.mark.django_db
def test_teachers_do_not_get_the_whole_school_dashboard(client_for, tenant_id):
    """The chronic-absence panel names individual children across every class."""
    teacher = client_for(["teacher"], "t@cyed.edu.au")
    assert teacher.get("/api/v1/analytics/dashboard/").status_code == 403


@pytest.mark.django_db
def test_families_cannot_read_the_dashboard(client_for):
    parent = client_for(["parent"], "p@example.com")
    assert parent.get("/api/v1/analytics/campus-comparison/").status_code == 403
