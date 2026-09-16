import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import ClassSection
from products.cyed.timetable.models import TimetableSlot


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def teacher_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "j.ellis@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["teacher"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_my_timetable_includes_slots_inherited_from_class_section(teacher_client, tenant_id):
    from products.cyed.hr.models import Staff

    staff = Staff.objects.create(
        tenant_id=tenant_id, first_name="Jamie", last_name="Ellis", email="j.ellis@cyed.edu.au",
    )
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Mathematics", teacher=staff)
    other_section = ClassSection.objects.create(tenant_id=tenant_id, name="9B Science")

    mine = TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=section, day_of_week="mon", period_label="Period 1",
    )
    not_mine = TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=other_section, day_of_week="mon", period_label="Period 2",
    )

    resp = teacher_client.get("/api/v1/timetable/slots/mine/")
    assert resp.status_code == 200, resp.data
    ids = {row["id"] for row in resp.data}
    assert str(mine.id) in ids
    assert str(not_mine.id) not in ids


@pytest.mark.django_db
def test_my_timetable_respects_per_slot_teacher_override(teacher_client, tenant_id):
    """A cover teacher on a single slot should see that slot even though the
    class's usual teacher is someone else — and the usual teacher should not."""
    from products.cyed.hr.models import Staff

    usual = Staff.objects.create(tenant_id=tenant_id, first_name="Priya", last_name="Rao",
                                  email="p.rao@cyed.edu.au")
    cover = Staff.objects.create(tenant_id=tenant_id, first_name="Jamie", last_name="Ellis",
                                  email="j.ellis@cyed.edu.au")
    section = ClassSection.objects.create(tenant_id=tenant_id, name="9B Science", teacher=usual)
    covered_slot = TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=section, day_of_week="tue", period_label="Period 3",
        teacher=cover,
    )

    resp = teacher_client.get("/api/v1/timetable/slots/mine/")
    assert resp.status_code == 200, resp.data
    ids = {row["id"] for row in resp.data}
    assert str(covered_slot.id) in ids


@pytest.mark.django_db
def test_conflict_detection_uses_teacher_link_not_name_string(platform_admin_client, tenant_id):
    """
    Two different staff who happen to share a name must both be bookable at
    the same time (they are different people); the same staff member must not
    be double-booked even if the two rows were typed with different-looking
    names. This is the bug the free-text `teacher_name` matching had.
    """
    from products.cyed.hr.models import Staff
    from products.cyed.hr.testing import clear_for_teaching

    same_name_a = Staff.objects.create(tenant_id=tenant_id, first_name="A", last_name="Nguyen")
    same_name_b = Staff.objects.create(tenant_id=tenant_id, first_name="A", last_name="Nguyen")
    # Assignment now requires a current WWCC and registration; without these
    # the timetable refuses the booking before conflict detection is reached.
    clear_for_teaching(same_name_a)
    clear_for_teaching(same_name_b)
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Mathematics")

    first = platform_admin_client.post(
        "/api/v1/timetable/slots/",
        {"class_section": str(section.id), "day_of_week": "wed", "period_label": "P1",
         "start_time": "09:00:00", "end_time": "10:00:00", "teacher": str(same_name_a.id)},
        format="json",
    )
    assert first.status_code == 201, first.data

    # Different person, same name, same window -> allowed.
    second = platform_admin_client.post(
        "/api/v1/timetable/slots/",
        {"class_section": str(section.id), "day_of_week": "wed", "period_label": "P1 (other room)",
         "start_time": "09:00:00", "end_time": "10:00:00", "teacher": str(same_name_b.id),
         "room": "B12"},
        format="json",
    )
    assert second.status_code == 201, second.data

    # Same person, overlapping window -> rejected.
    third = platform_admin_client.post(
        "/api/v1/timetable/slots/",
        {"class_section": str(section.id), "day_of_week": "wed", "period_label": "P1 clash",
         "start_time": "09:30:00", "end_time": "10:30:00", "teacher": str(same_name_a.id),
         "room": "C1"},
        format="json",
    )
    assert third.status_code == 400
    # Errors are rendered as RFC 7807 problem+json, so the field name and its
    # message land in `detail` rather than as a top-level key.
    assert "teacher" in third.data["detail"]
    assert "already timetabled" in third.data["detail"]
