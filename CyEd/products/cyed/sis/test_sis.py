import uuid

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
def test_enrol_student_into_class(platform_admin_client, tenant_id):
    # Create a guardian + student, link them.
    g = platform_admin_client.post(
        "/api/v1/sis/guardians/",
        {"first_name": "Sarah", "last_name": "Nguyen", "relationship": "mother"},
        format="json",
    )
    assert g.status_code == 201, g.data

    s = platform_admin_client.post(
        "/api/v1/sis/students/",
        {"first_name": "Minh", "last_name": "Nguyen", "year_level": 8,
         "enrolment_status": "enrolled", "guardians": [g.data["id"]]},
        format="json",
    )
    assert s.status_code == 201, s.data
    student_id = s.data["id"]

    c = platform_admin_client.post(
        "/api/v1/sis/class-sections/",
        {"name": "8A Mathematics", "subject": "Mathematics", "year_level": 8,
         "teacher_name": "Mr. Ellis"},
        format="json",
    )
    assert c.status_code == 201, c.data
    section_id = c.data["id"]

    e = platform_admin_client.post(
        "/api/v1/sis/enrolments/",
        {"student": student_id, "class_section": section_id, "status": "active"},
        format="json",
    )
    assert e.status_code == 201, e.data

    listed = platform_admin_client.get(f"/api/v1/sis/enrolments/?class_section={section_id}")
    rows = listed.data["results"] if isinstance(listed.data, dict) else listed.data
    assert len(rows) == 1
    assert str(rows[0]["student"]) == str(student_id)


@pytest.mark.django_db
def test_student_tenant_isolation(platform_admin_client, tenant_id):
    Student.objects.create(tenant_id=uuid.uuid4(), first_name="Foreign", last_name="Pupil")
    resp = platform_admin_client.get("/api/v1/sis/students/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["first_name"] != "Foreign" for r in rows)


@pytest.mark.django_db
def test_duplicate_enrolment_rejected(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=9)
    section = ClassSection.objects.create(tenant_id=tenant_id, name="9B Science", year_level=9)
    first = platform_admin_client.post(
        "/api/v1/sis/enrolments/",
        {"student": str(student.id), "class_section": str(section.id)},
        format="json",
    )
    assert first.status_code == 201, first.data
    dup = platform_admin_client.post(
        "/api/v1/sis/enrolments/",
        {"student": str(student.id), "class_section": str(section.id)},
        format="json",
    )
    assert dup.status_code == 400


@pytest.mark.django_db
def test_my_classes_returns_only_sections_linked_to_this_teacher(teacher_client, tenant_id):
    from products.cyed.hr.models import Staff

    staff = Staff.objects.create(
        tenant_id=tenant_id, first_name="Jamie", last_name="Ellis", email="j.ellis@cyed.edu.au",
    )
    other_staff = Staff.objects.create(
        tenant_id=tenant_id, first_name="Priya", last_name="Rao", email="p.rao@cyed.edu.au",
    )
    linked = ClassSection.objects.create(
        tenant_id=tenant_id, name="8A Mathematics", year_level=8, teacher=staff,
    )
    ClassSection.objects.create(
        tenant_id=tenant_id, name="9B Science", year_level=9, teacher=other_staff,
    )
    ClassSection.objects.create(
        # Legacy row: free-text name only, never backfilled to a Staff record.
        # Must NOT appear in "mine" — that's the whole point of the fix.
        tenant_id=tenant_id, name="10C History", year_level=10, teacher_name="Jamie Ellis",
    )

    resp = teacher_client.get("/api/v1/sis/class-sections/mine/")
    assert resp.status_code == 200, resp.data
    ids = {row["id"] for row in resp.data}
    assert ids == {str(linked.id)}


@pytest.mark.django_db
def test_my_classes_404s_when_account_has_no_linked_staff_record(teacher_client):
    resp = teacher_client.get("/api/v1/sis/class-sections/mine/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_teacher_display_prefers_linked_staff_over_legacy_name(tenant_id):
    from products.cyed.hr.models import Staff

    staff = Staff.objects.create(tenant_id=tenant_id, first_name="Jamie", last_name="Ellis")
    linked = ClassSection.objects.create(
        tenant_id=tenant_id, name="8A Mathematics", teacher=staff, teacher_name="Stale Name",
    )
    legacy = ClassSection.objects.create(
        tenant_id=tenant_id, name="9B Science", teacher_name="Ms. Rao",
    )
    assert linked.teacher_display() == "Jamie Ellis"
    assert legacy.teacher_display() == "Ms. Rao"
