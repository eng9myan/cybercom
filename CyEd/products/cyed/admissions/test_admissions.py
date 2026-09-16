import uuid

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
def test_application_offer_and_enrol(platform_admin_client, tenant_id):
    app = platform_admin_client.post(
        "/api/v1/admissions/applications/",
        {"applicant_first_name": "Noah", "applicant_last_name": "Park",
         "year_level_applying": 7, "guardian_name": "Jia Park", "status": "offer"},
        format="json",
    )
    assert app.status_code == 201, app.data
    app_id = app.data["id"]

    offer = platform_admin_client.post(
        "/api/v1/admissions/offers/",
        {"application": app_id, "offered_year_level": 7, "response": "accepted"},
        format="json",
    )
    assert offer.status_code == 201, offer.data

    enrolled = platform_admin_client.post(f"/api/v1/admissions/applications/{app_id}/enrol/")
    assert enrolled.status_code == 201, enrolled.data
    student_id = enrolled.data["student_id"]
    assert Student.objects.filter(id=student_id, tenant_id=tenant_id, enrolment_status="enrolled").exists()

    # Second enrol attempt is rejected. 409, not 400: the request is well
    # formed, it conflicts with the application's current state.
    again = platform_admin_client.post(f"/api/v1/admissions/applications/{app_id}/enrol/")
    assert again.status_code == 409


@pytest.mark.django_db
def test_application_status_filter(platform_admin_client, tenant_id):
    platform_admin_client.post(
        "/api/v1/admissions/applications/",
        {"applicant_first_name": "A", "applicant_last_name": "B", "status": "enquiry"},
        format="json",
    )
    platform_admin_client.post(
        "/api/v1/admissions/applications/",
        {"applicant_first_name": "C", "applicant_last_name": "D", "status": "submitted"},
        format="json",
    )
    resp = platform_admin_client.get("/api/v1/admissions/applications/?status=enquiry")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert rows[0]["status"] == "enquiry"
