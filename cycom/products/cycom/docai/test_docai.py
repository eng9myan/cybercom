"""
AI document parsing tests.

No real Anthropic API key exists in the test environment, so the
"not configured" path (extraction.py's actual, honest behavior with no key
set) is exercised for free and asserted directly -- exactly what a real
deployment sees before ANTHROPIC_API_KEY is provisioned. The "parsing
succeeded" path is tested by monkeypatching the extract() call the view
makes, not by hitting the network.
"""

import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from products.cycom.docai import extraction
from products.cycom.docai.models import ParsedDocument

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "ops@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["tenant_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _pdf():
    return SimpleUploadedFile("invoice.pdf", b"%PDF-1.4 fake bytes", content_type="application/pdf")


def test_upload_with_no_api_key_configured_fails_honestly_not_silently(admin_client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    resp = admin_client.post(
        "/api/v1/docai/documents/",
        {"document_type": "invoice", "file": _pdf()},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["status"] == "failed"
    assert "ANTHROPIC_API_KEY" in resp.data["error_message"]
    assert resp.data["extracted_data"] == {}


def test_upload_with_extraction_succeeding_stores_the_result(admin_client, monkeypatch):
    fake_result = {"vendor_name": "Acme Co", "invoice_number": "INV-1", "total_amount": 500.0}
    monkeypatch.setattr("products.cycom.docai.views.extract", lambda **kw: fake_result)

    resp = admin_client.post(
        "/api/v1/docai/documents/",
        {"document_type": "invoice", "file": _pdf()},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["status"] == "parsed"
    assert resp.data["extracted_data"] == fake_result
    assert resp.data["original_filename"] == "invoice.pdf"


def test_review_records_human_corrected_data_without_touching_extracted_data(admin_client, tenant_id):
    doc = ParsedDocument.objects.create(
        tenant_id=tenant_id, document_type="invoice", file=_pdf(),
        status="parsed", extracted_data={"total_amount": 500.0},
    )
    resp = admin_client.post(
        f"/api/v1/docai/documents/{doc.pk}/review/",
        {"reviewed_data": {"total_amount": 550.0}},
        format="json",
    )
    assert resp.status_code == 200
    doc.refresh_from_db()
    assert doc.status == "reviewed"
    assert doc.reviewed_data == {"total_amount": 550.0}
    assert doc.extracted_data == {"total_amount": 500.0}  # the AI's original output is preserved


def test_documents_list_returns_bare_array_not_paginated_envelope(admin_client, tenant_id):
    ParsedDocument.objects.create(tenant_id=tenant_id, document_type="invoice", file=_pdf())
    resp = admin_client.get("/api/v1/docai/documents/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)


def test_documents_are_tenant_isolated(admin_client):
    other_tenant = uuid.uuid4()
    theirs = ParsedDocument.objects.create(tenant_id=other_tenant, document_type="invoice", file=_pdf())
    resp = admin_client.get(f"/api/v1/docai/documents/{theirs.pk}/")
    assert resp.status_code == 404


def test_docai_endpoints_require_auth():
    anon = APIClient()
    assert anon.get("/api/v1/docai/documents/").status_code == 401


# -- extraction.py unit tests (no network) -----------------------------------

def test_extract_raises_not_configured_with_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(extraction.DocAIExtractionNotConfigured):
        extraction.extract(document_type="invoice", file_bytes=b"x", media_type="application/pdf")


def test_extract_rejects_an_unsupported_media_type(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with pytest.raises(extraction.DocAIExtractionError):
        extraction.extract(document_type="invoice", file_bytes=b"x", media_type="application/zip")


def test_extract_json_strips_a_markdown_fence():
    parsed = extraction._extract_json('```json\n{"a": 1}\n```')
    assert parsed == {"a": 1}


def test_extract_json_raises_on_no_json_found():
    with pytest.raises(extraction.DocAIExtractionError):
        extraction._extract_json("I could not read this document.")
