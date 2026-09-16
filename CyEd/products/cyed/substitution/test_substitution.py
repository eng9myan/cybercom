"""
Substitution engine.

The engine now reasons about `hr.Staff` rather than matching `teacher_name`
strings — the §0 finding the workflow audit opened with. These tests cover both
the behaviour that string matching could not express (two staff sharing a name;
clearance and absence checks on the cover pool) and the legacy path for slots
that were never linked to a Staff record.
"""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.hr.models import Staff
from products.cyed.hr.testing import clear_for_teaching
from products.cyed.sis.models import ClassSection
from products.cyed.timetable.models import TimetableSlot

MONDAY = date(2026, 8, 10)


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.fixture
def admin(client_for):
    return client_for(["tenant_admin"])


@pytest.fixture
def section(tenant_id):
    return ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)


def _staff(tenant_id, first, last, *, cleared=True):
    person = Staff.objects.create(
        tenant_id=tenant_id, first_name=first, last_name=last, role="teacher",
        email=f"{first.lower()}.{last.lower()}@cyed.edu.au",
    )
    if cleared:
        clear_for_teaching(person)
    return person


def _slot(tenant_id, section, staff, day, start, end, label="P1"):
    return TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=section, day_of_week=day, period_label=label,
        start_time=start, end_time=end, teacher=staff,
        teacher_name=f"{staff.first_name} {staff.last_name}".strip(),
    )


def _generate(client, staff, day="mon", **extra):
    body = {"absent_staff": str(staff.id), "day_of_week": day}
    body.update(extra)
    return client.post("/api/v1/substitution/plans/generate/", body, format="json")


# ── the core behaviour ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_free_colleague_is_proposed(admin, tenant_id, section):
    ellis = _staff(tenant_id, "Sam", "Ellis")
    cole = _staff(tenant_id, "Robin", "Cole")
    park = _staff(tenant_id, "Jo", "Park")

    _slot(tenant_id, section, ellis, "mon", "09:00", "10:00")
    _slot(tenant_id, section, cole, "mon", "09:00", "10:00")   # busy in that window
    _slot(tenant_id, section, park, "mon", "11:00", "12:00")   # free

    resp = _generate(admin, ellis)
    assert resp.status_code == 201, resp.data
    assignment = resp.data["assignments"][0]
    assert assignment["covered"] is True
    assert assignment["substitute_teacher"] == "Jo Park"
    assert resp.data["covered_count"] == 1


@pytest.mark.django_db
def test_a_gap_explains_itself(admin, tenant_id, section):
    """A bare 'uncovered' sends a human back through the timetable to find out why."""
    ellis = _staff(tenant_id, "Sam", "Ellis")
    cole = _staff(tenant_id, "Robin", "Cole")
    _slot(tenant_id, section, ellis, "mon", "09:00", "10:00")
    _slot(tenant_id, section, cole, "mon", "09:00", "10:00")

    resp = _generate(admin, ellis)
    assignment = resp.data["assignments"][0]
    assert assignment["covered"] is False
    assert assignment["substitute_teacher"] == ""
    assert "teaching in this window" in assignment["gap_reason"]
    assert resp.data["gap_count"] == 1


@pytest.mark.django_db
def test_load_is_balanced_across_the_day(admin, tenant_id, section):
    """One willing colleague must not absorb the whole day."""
    ellis = _staff(tenant_id, "Sam", "Ellis")
    _staff(tenant_id, "Robin", "Cole")
    _staff(tenant_id, "Jo", "Park")

    for i, (start, end) in enumerate([("09:00", "10:00"), ("10:00", "11:00")]):
        _slot(tenant_id, section, ellis, "mon", start, end, label=f"P{i + 1}")

    resp = _generate(admin, ellis)
    substitutes = {a["substitute_teacher"] for a in resp.data["assignments"]}
    assert len(substitutes) == 2      # spread, not doubled up


@pytest.mark.django_db
def test_reruns_produce_the_same_sheet(admin, tenant_id, section):
    ellis = _staff(tenant_id, "Sam", "Ellis")
    _staff(tenant_id, "Robin", "Cole")
    _staff(tenant_id, "Jo", "Park")
    _slot(tenant_id, section, ellis, "mon", "09:00", "10:00")

    first = _generate(admin, ellis).data["assignments"][0]["substitute_teacher"]
    second = _generate(admin, ellis).data["assignments"][0]["substitute_teacher"]
    assert first == second


# ── what string matching could not do ────────────────────────────────────────
@pytest.mark.django_db
def test_two_staff_sharing_a_name_are_different_people(admin, tenant_id, section):
    """
    The original bug: "A. Nguyen" and "Anh Nguyen" were different people, and
    two staff with the same name were one.
    """
    absent = _staff(tenant_id, "Anh", "Nguyen")
    namesake = Staff.objects.create(
        tenant_id=tenant_id, first_name="Anh", last_name="Nguyen",
        role="teacher", email="anh.nguyen2@cyed.edu.au",
    )
    clear_for_teaching(namesake)

    _slot(tenant_id, section, absent, "mon", "09:00", "10:00")

    resp = _generate(admin, absent)
    assignment = resp.data["assignments"][0]
    # The namesake is free and must be offered — they are not the absent person.
    assert assignment["covered"] is True
    assert str(assignment["substitute_staff"]) == str(namesake.id)


@pytest.mark.django_db
def test_an_uncleared_colleague_is_not_offered_cover(admin, tenant_id, section):
    """
    Cover is exactly the situation where an uncleared adult ends up in front of
    a class at short notice.
    """
    ellis = _staff(tenant_id, "Sam", "Ellis")
    _staff(tenant_id, "Jo", "Park", cleared=False)
    _slot(tenant_id, section, ellis, "mon", "09:00", "10:00")

    resp = _generate(admin, ellis)
    assignment = resp.data["assignments"][0]
    assert assignment["covered"] is False
    assert "clearance not current" in assignment["gap_reason"]


@pytest.mark.django_db
def test_a_colleague_who_is_also_away_cannot_cover(admin, tenant_id, section):
    from products.cyed.staff_attendance.models import StaffAttendanceDay

    ellis = _staff(tenant_id, "Sam", "Ellis")
    park = _staff(tenant_id, "Jo", "Park")
    _slot(tenant_id, section, ellis, "mon", "09:00", "10:00")
    StaffAttendanceDay.objects.create(
        tenant_id=tenant_id, staff=park, date=MONDAY, status="sick"
    )

    resp = _generate(admin, ellis, date=MONDAY.isoformat())
    assignment = resp.data["assignments"][0]
    assert assignment["covered"] is False
    assert "already absent" in assignment["gap_reason"]


@pytest.mark.django_db
def test_classes_inherited_from_the_class_section_are_covered_too(admin, tenant_id):
    """A timetable row often leaves the teacher implicit on the section."""
    ellis = _staff(tenant_id, "Sam", "Ellis")
    _staff(tenant_id, "Jo", "Park")
    section = ClassSection.objects.create(
        tenant_id=tenant_id, name="9B", year_level=9, teacher=ellis
    )
    TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=section, day_of_week="mon",
        period_label="P1", start_time="09:00", end_time="10:00",
    )
    resp = _generate(admin, ellis)
    assert len(resp.data["assignments"]) == 1
    assert resp.data["assignments"][0]["covered"] is True


# ── legacy name path ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_an_unambiguous_name_still_resolves(admin, tenant_id, section):
    ellis = _staff(tenant_id, "Sam", "Ellis")
    _staff(tenant_id, "Jo", "Park")
    _slot(tenant_id, section, ellis, "mon", "09:00", "10:00")

    resp = admin.post("/api/v1/substitution/plans/generate/", {
        "absent_teacher": "Sam Ellis", "day_of_week": "mon",
    }, format="json")
    assert resp.status_code == 201
    assert resp.data["assignments"][0]["covered"] is True


@pytest.mark.django_db
def test_unlinked_legacy_slots_are_still_found_by_name(admin, tenant_id, section):
    """Rows that were never backfilled to a Staff record must not vanish."""
    _staff(tenant_id, "Jo", "Park")
    TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=section, day_of_week="mon",
        period_label="P1", start_time="09:00", end_time="10:00",
        teacher_name="Mr Legacy",
    )
    resp = admin.post("/api/v1/substitution/plans/generate/", {
        "absent_teacher": "Mr Legacy", "day_of_week": "mon",
    }, format="json")
    assert resp.status_code == 201
    assert len(resp.data["assignments"]) == 1


# ── the pool itself ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_cover_pool_reports_why_people_were_ruled_out(admin, tenant_id):
    _staff(tenant_id, "Jo", "Park")
    _staff(tenant_id, "No", "Clearance", cleared=False)

    resp = admin.get("/api/v1/substitution/plans/cover-pool/")
    assert resp.status_code == 200
    assert [e["name"] for e in resp.data["eligible"]] == ["Jo Park"]
    assert resp.data["excluded"][0]["reason"] == "clearance not current"


@pytest.mark.django_db
def test_generate_requires_a_teacher_and_a_day(admin):
    resp = admin.post(
        "/api/v1/substitution/plans/generate/", {"day_of_week": "mon"}, format="json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_generate_is_staff_only(client_for):
    parent = client_for(["parent"], email="p@home.com")
    assert parent.post("/api/v1/substitution/plans/generate/",
                       {"absent_teacher": "X", "day_of_week": "mon"},
                       format="json").status_code == 403
