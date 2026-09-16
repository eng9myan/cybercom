import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="u@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.mark.django_db
def test_health_confidential_pastoral_only(client_for, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)

    teacher = client_for(["teacher"])
    assert teacher.get("/api/v1/health/records/").status_code == 403

    nurse = client_for(["counsellor"])  # pastoral/health role
    created = nurse.post("/api/v1/health/records/",
                         {"student": str(student.id), "allergies": "Peanuts", "blood_type": "O+"}, format="json")
    assert created.status_code == 201, created.data
    assert nurse.get("/api/v1/health/records/").status_code == 200
