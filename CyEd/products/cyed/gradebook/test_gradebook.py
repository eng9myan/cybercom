import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.gradebook.models import Assessment
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
def test_record_grade_and_percentage(platform_admin_client, tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Maths", year_level=8)
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)

    a = platform_admin_client.post(
        "/api/v1/gradebook/assessments/",
        {"class_section": str(section.id), "name": "Fractions Quiz",
         "assessment_type": "formative", "max_score": "20", "curriculum_code": "AC9M8N01"},
        format="json",
    )
    assert a.status_code == 201, a.data
    assessment_id = a.data["id"]

    g = platform_admin_client.post(
        "/api/v1/gradebook/grades/",
        {"assessment": assessment_id, "student": str(student.id), "score": "15",
         "achievement_level": "B"},
        format="json",
    )
    assert g.status_code == 201, g.data
    assert g.data["percentage"] == 75.0

    listed = platform_admin_client.get(f"/api/v1/gradebook/grades/?assessment={assessment_id}")
    rows = listed.data["results"] if isinstance(listed.data, dict) else listed.data
    assert len(rows) == 1


@pytest.mark.django_db
def test_assessment_tenant_isolation(platform_admin_client, tenant_id):
    other = uuid.uuid4()
    section = ClassSection.objects.create(tenant_id=other, name="Foreign Class", year_level=8)
    Assessment.objects.create(tenant_id=other, class_section=section, name="Foreign Exam")
    resp = platform_admin_client.get("/api/v1/gradebook/assessments/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign Exam" for r in rows)
