import hashlib
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from products.cyvault.files.models import FileObject


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
def test_upload_returns_real_download_url_and_checksum(platform_admin_client):
    content = b"fake dicom study bytes"
    f = SimpleUploadedFile("study.dcm", content, content_type="application/dicom")
    resp = platform_admin_client.post(
        "/api/v1/files/files/",
        {"file": f, "original_filename": "study.dcm", "category": "dicom_study"},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["download_url"]  # real URL from the active storage backend
    assert body["size_bytes"] == len(content)
    assert body["checksum_sha256"] == hashlib.sha256(content).hexdigest()

    # Real round-trip: fetch the file back through the storage backend and
    # confirm the bytes match what was uploaded, not just that a row exists.
    obj = FileObject.objects.get(id=body["id"])
    obj.file.open("rb")
    try:
        assert obj.file.read() == content
    finally:
        obj.file.close()


@pytest.mark.django_db
def test_linked_dicom_study_filter(platform_admin_client, tenant_id):
    study_id = uuid.uuid4()
    FileObject.objects.create(
        tenant_id=tenant_id,
        file="cyvault/study.dcm",
        original_filename="study.dcm",
        category="dicom_study",
        linked_model="cymed.imaging.study",
        linked_id=study_id,
    )
    FileObject.objects.create(
        tenant_id=tenant_id,
        file="cyvault/unrelated.pdf",
        original_filename="unrelated.pdf",
        category="generic",
    )

    resp = platform_admin_client.get(
        f"/api/v1/files/files/?linked_model=cymed.imaging.study&linked_id={study_id}"
    )
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["original_filename"] == "study.dcm"


@pytest.mark.django_db
def test_tenant_isolation(mint_token, mock_jwks, tenant_id):
    other_tenant_id = uuid.uuid4()
    FileObject.objects.create(
        tenant_id=other_tenant_id,
        file="cyvault/other.pdf",
        original_filename="other.pdf",
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
    resp = client.get("/api/v1/files/files/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0
