import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from products.cyed.intake.extract import extract_fields


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def test_extract_fields_from_text():
    text = "Name: Minh Nguyen\nDate of Birth: 14/03/2012\nRegistration No: BC-99381"
    f = extract_fields(text, "birth_certificate")
    assert f["name"] == "Minh Nguyen"
    assert f["date_of_birth"] == "14/03/2012"
    assert f["document_number"] == "BC-99381"


@pytest.mark.django_db
def test_upload_text_extracts(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    payload = SimpleUploadedFile("bc.txt", b"Name: Ivy Chen\nNumber: ID-7712", content_type="text/plain")
    resp = admin.post("/api/v1/intake/documents/", {"doc_type": "id", "file": payload}, format="multipart")
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "extracted"
    assert resp.data["extracted_fields"]["name"] == "Ivy Chen"
    assert resp.data["extracted_fields"]["document_number"] == "ID-7712"


@pytest.mark.django_db
def test_raw_text_post_and_reprocess(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    created = admin.post("/api/v1/intake/documents/",
                         {"doc_type": "transcript", "raw_text": "Name: Ava Lee"}, format="json")
    assert created.status_code == 201
    assert created.data["extracted_fields"]["name"] == "Ava Lee"

    doc_id = created.data["id"]
    re = admin.post(f"/api/v1/intake/documents/{doc_id}/reprocess/",
                    {"raw_text": "Name: Ava Marie Lee\nNo: TR-001"}, format="json")
    assert re.data["extracted_fields"]["document_number"] == "TR-001"


@pytest.mark.django_db
def test_intake_staff_only(client_for, tenant_id):
    parent = client_for(["parent"], email="p@home.com")
    assert parent.post("/api/v1/intake/documents/", {"doc_type": "id", "raw_text": "x"},
                       format="json").status_code == 403
