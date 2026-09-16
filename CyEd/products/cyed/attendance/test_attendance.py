import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import ClassSection, Student


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


@pytest.mark.django_db
def test_roll_call_and_marks(platform_admin_client, tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Maths", year_level=8)
    s1 = Student.objects.create(tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=8)
    s2 = Student.objects.create(tenant_id=tenant_id, first_name="Ben", last_name="Ng", year_level=8)

    rc = platform_admin_client.post(
        "/api/v1/attendance/roll-calls/",
        {"class_section": str(section.id), "date": str(date.today()), "period_label": "Period 1"},
        format="json",
    )
    assert rc.status_code == 201, rc.data
    roll_id = rc.data["id"]

    m1 = platform_admin_client.post(
        "/api/v1/attendance/marks/",
        {"roll_call": roll_id, "student": str(s1.id), "status": "present"},
        format="json",
    )
    assert m1.status_code == 201, m1.data
    m2 = platform_admin_client.post(
        "/api/v1/attendance/marks/",
        {"roll_call": roll_id, "student": str(s2.id), "status": "absent"},
        format="json",
    )
    assert m2.status_code == 201, m2.data

    rc_detail = platform_admin_client.get(f"/api/v1/attendance/roll-calls/{roll_id}/")
    assert rc_detail.data["present_count"] == 1
    assert rc_detail.data["absent_count"] == 1


@pytest.mark.django_db
def test_duplicate_mark_rejected(platform_admin_client, tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Maths", year_level=8)
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=8)
    rc = platform_admin_client.post(
        "/api/v1/attendance/roll-calls/",
        {"class_section": str(section.id), "date": str(date.today())},
        format="json",
    )
    roll_id = rc.data["id"]
    first = platform_admin_client.post(
        "/api/v1/attendance/marks/",
        {"roll_call": roll_id, "student": str(student.id), "status": "present"},
        format="json",
    )
    assert first.status_code == 201
    dup = platform_admin_client.post(
        "/api/v1/attendance/marks/",
        {"roll_call": roll_id, "student": str(student.id), "status": "late"},
        format="json",
    )
    assert dup.status_code == 400
