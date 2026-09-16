import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.reporting.models import ReportCard, ReportCardDocument
from products.cyed.sis.models import Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token(
            {"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
             "realm_access": {"roles": roles}}
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def _report_with_entry(admin, student_id):
    rc = admin.post("/api/v1/reporting/report-cards/", {"student": student_id, "term": "Semester 1"}, format="json")
    card_id = rc.data["id"]
    admin.post("/api/v1/reporting/entries/",
               {"report_card": card_id, "subject": "Mathematics", "achievement": "B", "effort": "high",
                "comment": "Strong progress."}, format="json")
    return card_id


@pytest.mark.django_db
def test_publish_creates_verified_immutable_pdf(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    card_id = _report_with_entry(admin, str(student.id))

    pub = admin.post(f"/api/v1/reporting/report-cards/{card_id}/publish/")
    assert pub.status_code == 200
    assert pub.data["document"]["version"] == 1
    assert pub.data["document"]["verified"] is True

    # Document metadata verifies; PDF downloads and is a real PDF.
    meta = admin.get(f"/api/v1/reporting/report-cards/{card_id}/document/")
    assert meta.status_code == 200
    assert meta.data["verified"] is True
    assert len(meta.data["content_hash"]) == 64

    pdf = admin.get(f"/api/v1/reporting/report-cards/{card_id}/pdf/")
    assert pdf.status_code == 200
    assert pdf["Content-Type"] == "application/pdf"
    assert pdf.content[:5] == b"%PDF-"


@pytest.mark.django_db
def test_tamper_is_detected(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    card_id = _report_with_entry(admin, str(student.id))
    admin.post(f"/api/v1/reporting/report-cards/{card_id}/publish/")

    doc = ReportCardDocument.objects.get(report_card_id=card_id, version=1)
    assert doc.verify() is True
    # Tamper with the frozen snapshot — the hash no longer matches.
    doc.snapshot["entries"][0]["achievement"] = "A"
    doc.save(update_fields=["snapshot"])
    assert doc.verify() is False


@pytest.mark.django_db
def test_republish_creates_new_version_retaining_old(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    card_id = _report_with_entry(admin, str(student.id))
    admin.post(f"/api/v1/reporting/report-cards/{card_id}/publish/")

    # Amend an entry, then re-publish → version 2, version 1 retained.
    entry = admin.get(f"/api/v1/reporting/entries/?report_card={card_id}").data
    entry_id = (entry["results"] if isinstance(entry, dict) else entry)[0]["id"]
    admin.patch(f"/api/v1/reporting/entries/{entry_id}/", {"achievement": "A"}, format="json")

    pub2 = admin.post(f"/api/v1/reporting/report-cards/{card_id}/publish/")
    assert pub2.data["document"]["version"] == 2
    assert ReportCardDocument.objects.filter(report_card_id=card_id).count() == 2
    v1 = ReportCardDocument.objects.get(report_card_id=card_id, version=1)
    assert v1.snapshot["entries"][0]["achievement"] == "B"  # original preserved


@pytest.mark.django_db
def test_parent_can_acknowledge_own_child_only(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    mine = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    guardian = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Chen",
                                       email="parent@home.com")
    guardian.students.add(mine)
    card_id = _report_with_entry(admin, str(mine.id))
    admin.post(f"/api/v1/reporting/report-cards/{card_id}/publish/")

    parent = client_for(["parent"], email="parent@home.com")
    ack = parent.post(f"/api/v1/reporting/report-cards/{card_id}/acknowledge/")
    assert ack.status_code == 200
    assert ack.data["acknowledged_by"] == "parent@home.com"

    # A different parent cannot even see / acknowledge it.
    other = client_for(["parent"], email="other@home.com")
    assert other.post(f"/api/v1/reporting/report-cards/{card_id}/acknowledge/").status_code == 404


@pytest.mark.django_db
def test_document_404_before_publish(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    student = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    card_id = _report_with_entry(admin, str(student.id))
    assert admin.get(f"/api/v1/reporting/report-cards/{card_id}/document/").status_code == 404
