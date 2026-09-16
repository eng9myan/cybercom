import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import Student


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
def test_learner_profile_eald_and_uniqueness(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)

    resp = platform_admin_client.post(
        "/api/v1/wellbeing/learner-profiles/",
        {"student": str(student.id), "eald_level": "DV", "first_language": "Vietnamese",
         "is_neurodivergent": True, "accommodations": "Extra time; chunked tasks"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["eald_level"] == "DV"

    # OneToOne — a second profile for the same student is rejected cleanly.
    dup = platform_admin_client.post(
        "/api/v1/wellbeing/learner-profiles/",
        {"student": str(student.id), "eald_level": "CO"},
        format="json",
    )
    assert dup.status_code == 400


@pytest.mark.django_db
def test_behaviour_incident_filter(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=9)
    platform_admin_client.post(
        "/api/v1/wellbeing/behaviour-incidents/",
        {"student": str(student.id), "date": str(date.today()), "category": "positive",
         "description": "Helped a peer"},
        format="json",
    )
    platform_admin_client.post(
        "/api/v1/wellbeing/behaviour-incidents/",
        {"student": str(student.id), "date": str(date.today()), "category": "minor",
         "description": "Late to class"},
        format="json",
    )
    resp = platform_admin_client.get(f"/api/v1/wellbeing/behaviour-incidents/?student={student.id}&category=positive")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert rows[0]["category"] == "positive"
