"""
Multi-campus: scoping and transfer history.

A 13-campus group runs as one tenant, so tenant isolation alone lets a
Northside receptionist read Southside's students. `scope_queryset_by_campus`
had existed for this and was wired into nothing — the most expensive kind of
security control, because it looks present in review.
"""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.org.models import Campus
from products.cyed.sis.models import CampusTransfer, ClassSection, Enrolment, Student
from products.cyed.sis.transfers import TransferError, campus_on, transfer_student


@pytest.fixture
def campuses(tenant_id):
    north = Campus.objects.create(tenant_id=tenant_id, name="Northside", code="NTH")
    south = Campus.objects.create(tenant_id=tenant_id, name="Southside", code="STH")
    return north, south


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, *, email="user@cyed.edu.au", campus_ids=None):
        claims = {
            "sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
            "realm_access": {"roles": roles},
        }
        if campus_ids is not None:
            claims["campus_ids"] = [str(c) for c in campus_ids]
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token(claims)}")
        return c
    return _make


@pytest.fixture
def students(tenant_id, campuses):
    north, south = campuses
    n = Student.objects.create(
        tenant_id=tenant_id, first_name="Nina", last_name="North",
        year_level=5, enrolment_status="enrolled", campus=north,
    )
    s = Student.objects.create(
        tenant_id=tenant_id, first_name="Sam", last_name="South",
        year_level=5, enrolment_status="enrolled", campus=south,
    )
    unassigned = Student.objects.create(
        tenant_id=tenant_id, first_name="Group", last_name="Wide",
        year_level=5, enrolment_status="enrolled",
    )
    return n, s, unassigned


# ── scoping ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_campus_bound_staff_see_only_their_campus(client_for, campuses, students):
    north, _ = campuses
    receptionist = client_for(["teacher"], campus_ids=[north.id])
    resp = receptionist.get("/api/v1/sis/students/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    names = {r["first_name"] for r in rows}
    assert "Nina" in names
    assert "Sam" not in names


@pytest.mark.django_db
def test_group_level_records_stay_visible_to_campus_staff(client_for, campuses, students):
    """
    A row with no campus is group-level data. Hiding it would make a campus
    user's world look emptier than it is — that reads as data loss, not scoping.
    """
    north, _ = campuses
    receptionist = client_for(["teacher"], campus_ids=[north.id])
    resp = receptionist.get("/api/v1/sis/students/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert "Group" in {r["first_name"] for r in rows}


@pytest.mark.django_db
def test_leadership_sees_every_campus(client_for, campuses, students):
    principal = client_for(["leadership"])
    resp = principal.get("/api/v1/sis/students/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert {"Nina", "Sam", "Group"} <= {r["first_name"] for r in rows}


@pytest.mark.django_db
def test_a_campus_user_cannot_fetch_another_campus_student_directly(
    client_for, campuses, students
):
    """Scoping the list but not the detail route would be no scoping at all."""
    north, _ = campuses
    _, sam, _unassigned = students
    receptionist = client_for(["teacher"], campus_ids=[north.id])
    assert receptionist.get(f"/api/v1/sis/students/{sam.id}/").status_code == 404


@pytest.mark.django_db
def test_class_sections_are_campus_scoped(client_for, tenant_id, campuses):
    north, south = campuses
    ClassSection.objects.create(tenant_id=tenant_id, name="5N", year_level=5, campus=north)
    ClassSection.objects.create(tenant_id=tenant_id, name="5S", year_level=5, campus=south)

    resp = client_for(["teacher"], campus_ids=[north.id]).get("/api/v1/sis/class-sections/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert {r["name"] for r in rows} == {"5N"}


@pytest.mark.django_db
def test_staff_are_campus_scoped(client_for, tenant_id, campuses):
    from products.cyed.hr.models import Staff

    north, south = campuses
    Staff.objects.create(tenant_id=tenant_id, first_name="Nora", last_name="N", campus=north)
    Staff.objects.create(tenant_id=tenant_id, first_name="Seth", last_name="S", campus=south)

    resp = client_for(["teacher"], campus_ids=[north.id]).get("/api/v1/hr/staff/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert {r["first_name"] for r in rows} == {"Nora"}


@pytest.mark.django_db
def test_rolls_are_scoped_through_their_class_section(client_for, tenant_id, campuses):
    from products.cyed.attendance.models import RollCall

    north, south = campuses
    n_section = ClassSection.objects.create(
        tenant_id=tenant_id, name="5N", year_level=5, campus=north
    )
    s_section = ClassSection.objects.create(
        tenant_id=tenant_id, name="5S", year_level=5, campus=south
    )
    RollCall.objects.create(tenant_id=tenant_id, class_section=n_section, date=date(2026, 8, 11))
    RollCall.objects.create(tenant_id=tenant_id, class_section=s_section, date=date(2026, 8, 11))

    resp = client_for(["teacher"], campus_ids=[north.id]).get("/api/v1/attendance/roll-calls/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1


# ── transfers ────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_transfer_is_recorded_not_just_applied(tenant_id, campuses, students):
    """
    The question a bare FK could not answer: which campus was this child at
    in March?
    """
    north, south = campuses
    nina, _, _ = students
    transfer_student(
        nina, to_campus=south, effective_on=date(2026, 7, 21), reason="Family relocated"
    )

    nina.refresh_from_db()
    assert nina.campus_id == south.id
    record = CampusTransfer.objects.get(student=nina)
    assert record.from_campus_id == north.id
    assert record.to_campus_id == south.id
    assert record.reason == "Family relocated"


@pytest.mark.django_db
def test_campus_on_a_past_date_reads_the_history(tenant_id, campuses, students):
    north, south = campuses
    nina, _, _ = students
    transfer_student(nina, to_campus=south, effective_on=date(2026, 7, 21))

    assert campus_on(nina, date(2026, 3, 1)).id == north.id   # before the move
    assert campus_on(nina, date(2026, 7, 21)).id == south.id  # on the day
    assert campus_on(nina, date(2026, 9, 1)).id == south.id   # after


@pytest.mark.django_db
def test_a_student_who_never_moved_reports_their_current_campus(campuses, students):
    north, _ = campuses
    nina, _, _ = students
    assert campus_on(nina, date(2026, 3, 1)).id == north.id


@pytest.mark.django_db
def test_transfer_ends_placements_at_the_campus_being_left(tenant_id, campuses, students):
    """
    Carrying the placement across would leave the child on a roll at a site
    they no longer attend, and invisible to their new teachers.
    """
    north, south = campuses
    nina, _, _ = students
    old_class = ClassSection.objects.create(
        tenant_id=tenant_id, name="5N", year_level=5, campus=north
    )
    group_elective = ClassSection.objects.create(
        tenant_id=tenant_id, name="Online Japanese", year_level=5
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=nina, class_section=old_class, status="active"
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=nina, class_section=group_elective, status="active"
    )

    record = transfer_student(nina, to_campus=south)
    assert record.enrolments_ended == 1
    assert Enrolment.objects.get(student=nina, class_section=old_class).status == "completed"
    # A group-wide section has no campus and is not disturbed.
    assert Enrolment.objects.get(student=nina, class_section=group_elective).status == "active"


@pytest.mark.django_db
def test_live_bills_follow_the_student(tenant_id, campuses, students):
    from products.cyed.billing.models import StudentBill

    north, south = campuses
    nina, _, _ = students
    live = StudentBill.objects.create(
        tenant_id=tenant_id, student=nina, campus=north, status="active"
    )
    settled = StudentBill.objects.create(
        tenant_id=tenant_id, student=nina, campus=north, status="settled"
    )

    transfer_student(nina, to_campus=south)

    live.refresh_from_db()
    settled.refresh_from_db()
    assert live.campus_id == south.id
    # A settled bill keeps the campus that earned the money.
    assert settled.campus_id == north.id


@pytest.mark.django_db
def test_transferring_to_the_same_campus_is_refused(campuses, students):
    north, _ = campuses
    nina, _, _ = students
    with pytest.raises(TransferError, match="already at Northside"):
        transfer_student(nina, to_campus=north)


@pytest.mark.django_db
def test_transfer_endpoint_and_history(client_for, campuses, students):
    north, south = campuses
    nina, _, _ = students
    admin = client_for(["tenant_admin"], email="registrar@cyed.edu.au")

    resp = admin.post(f"/api/v1/sis/students/{nina.id}/transfer-campus/", {
        "to_campus": str(south.id), "effective_on": "2026-07-21",
        "reason": "Family relocated",
    }, format="json")
    assert resp.status_code == 201, resp.data

    history = admin.get(f"/api/v1/sis/students/{nina.id}/campus-history/")
    assert history.status_code == 200
    assert len(history.data["transfers"]) == 1
    assert history.data["transfers"][0]["to_campus"] == "Southside"
    assert history.data["current_campus"] == str(south.id)
