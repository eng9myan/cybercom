import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from products.cycom.documents.models import Document


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_upload_and_tag_search(platform_admin_client, tenant_id):
    f = SimpleUploadedFile("invoice.pdf", b"fake pdf bytes", content_type="application/pdf")
    resp = platform_admin_client.post(
        "/api/v1/documents/documents/",
        {"title": "Vendor Invoice", "file": f, "tags": '["invoice", "vendor-x"]'},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content

    resp = platform_admin_client.get("/api/v1/documents/documents/?tag=vendor-x")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_linked_record_filter(platform_admin_client, tenant_id):
    linked_id = uuid.uuid4()
    Document.objects.create(
        tenant_id=tenant_id,
        title="AP Bill Attachment",
        file="cycom_documents/bill.pdf",
        linked_model="ar_ap.Bill",
        linked_id=linked_id,
    )
    Document.objects.create(
        tenant_id=tenant_id,
        title="Unrelated",
        file="cycom_documents/other.pdf",
    )

    resp = platform_admin_client.get(
        f"/api/v1/documents/documents/?linked_model=ar_ap.Bill&linked_id={linked_id}"
    )
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["title"] == "AP Bill Attachment"


@pytest.mark.django_db
def test_tenant_isolation(mint_token, mock_jwks, tenant_id):
    other_tenant_id = uuid.uuid4()
    Document.objects.create(
        tenant_id=other_tenant_id, title="Other Tenant Doc", file="cycom_documents/x.pdf"
    )

    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "user@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": []},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    resp = client.get("/api/v1/documents/documents/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0
