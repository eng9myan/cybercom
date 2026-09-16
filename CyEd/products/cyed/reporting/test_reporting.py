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
def test_report_card_entries_and_publish(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)

    rc = platform_admin_client.post(
        "/api/v1/reporting/report-cards/",
        {"student": str(student.id), "term": "Semester 1"},
        format="json",
    )
    assert rc.status_code == 201, rc.data
    assert rc.data["status"] == "draft"
    card_id = rc.data["id"]

    e = platform_admin_client.post(
        "/api/v1/reporting/entries/",
        {"report_card": card_id, "subject": "Mathematics", "achievement": "B",
         "effort": "high", "comment": "Strong progress on number."},
        format="json",
    )
    assert e.status_code == 201, e.data

    pub = platform_admin_client.post(f"/api/v1/reporting/report-cards/{card_id}/publish/")
    assert pub.status_code == 200
    assert pub.data["status"] == "published"
    assert pub.data["published_on"] is not None
    assert len(pub.data["entries"]) == 1


@pytest.mark.django_db
def test_duplicate_subject_entry_rejected(platform_admin_client, tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    rc = platform_admin_client.post(
        "/api/v1/reporting/report-cards/",
        {"student": str(student.id), "term": "Semester 1"},
        format="json",
    )
    card_id = rc.data["id"]
    first = platform_admin_client.post(
        "/api/v1/reporting/entries/",
        {"report_card": card_id, "subject": "Mathematics", "achievement": "B"},
        format="json",
    )
    assert first.status_code == 201
    dup = platform_admin_client.post(
        "/api/v1/reporting/entries/",
        {"report_card": card_id, "subject": "Mathematics", "achievement": "C"},
        format="json",
    )
    assert dup.status_code == 400
