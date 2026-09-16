import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.gradebook.models import Assessment, Grade
from products.cyed.sis.models import ClassSection, Student


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "registrar@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_export_returns_full_record(platform_admin_client, tenant_id):
    student = Student.objects.create(
        tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8,
        student_number="S0001", email="minh@example.com",
    )
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    a = Assessment.objects.create(tenant_id=tenant_id, class_section=section, name="Quiz", max_score=20)
    Grade.objects.create(tenant_id=tenant_id, assessment=a, student=student, score=15)

    resp = platform_admin_client.get(f"/api/v1/sis/students/{student.id}/export/")
    assert resp.status_code == 200, resp.data
    for key in ("student", "guardians", "enrolments", "grades", "attendance", "invoices", "report_cards"):
        assert key in resp.data
    assert len(resp.data["grades"]) == 1


@pytest.mark.django_db
def test_deidentify_strips_pii(platform_admin_client, tenant_id):
    student = Student.objects.create(
        tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8,
        student_number="S0001", email="minh@example.com",
    )
    resp = platform_admin_client.post(f"/api/v1/sis/students/{student.id}/deidentify/")
    assert resp.status_code == 200, resp.data
    student.refresh_from_db()
    assert student.first_name == "De-identified"
    assert student.email == ""
    assert student.student_number == ""
    assert student.date_of_birth is None
    assert student.enrolment_status == "withdrawn"
