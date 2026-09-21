import json
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from products.cycom.esign.models import SignRequest, SignTemplate


@pytest.fixture
def auth_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "ops@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def template(db, tenant_id):
    return SignTemplate.objects.create(
        tenant_id=tenant_id,
        name="NDA",
        file="cycom_esign/templates/nda.pdf",
        fields_config=[{"type": "signature", "label": "Signature Block", "page": 1, "x": 100, "y": 600}],
    )


@pytest.mark.django_db
def test_upload_template_multipart_parses_fields_config(auth_client):
    f = SimpleUploadedFile("nda.pdf", b"%PDF-fake", content_type="application/pdf")
    fields_config = [{"type": "signature", "label": "Sig", "page": 1, "x": 100, "y": 600}]
    resp = auth_client.post(
        "/api/sign/templates/",
        {"name": "Vendor NDA", "file": f, "fields_config": json.dumps(fields_config)},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["fields_config"] == fields_config


@pytest.mark.django_db
def test_list_templates_is_bare_array_not_paginated(auth_client, template):
    resp = auth_client.get("/api/sign/templates/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    assert resp.data[0]["name"] == "NDA"


@pytest.mark.django_db
def test_create_request_generates_token(auth_client, template):
    resp = auth_client.post(
        "/api/sign/requests/",
        {"template_id": str(template.id), "signers": [{"name": "Jane Doe", "email": "jane@x.com"}]},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.data["status"] == "Sent"
    assert len(resp.data["token"]) > 20


@pytest.mark.django_db
def test_list_requests_is_bare_array(auth_client, template):
    SignRequest.objects.create(
        tenant_id=template.tenant_id, template=template, signers=[{"name": "A", "email": "a@x.com"}]
    )
    resp = auth_client.get("/api/sign/requests/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)


@pytest.mark.django_db
def test_tenant_isolation_on_requests(mint_token, mock_jwks, tenant_id, template):
    SignRequest.objects.create(
        tenant_id=template.tenant_id, template=template, signers=[{"name": "A", "email": "a@x.com"}]
    )
    other_token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "other@cybercom.io",
            "tenant_id": str(uuid.uuid4()),
            "realm_access": {"roles": []},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token}")
    resp = client.get("/api/sign/requests/")
    assert resp.status_code == 200
    assert resp.data == []


@pytest.mark.django_db
def test_public_detail_flips_sent_to_viewed(template):
    req = SignRequest.objects.create(
        tenant_id=template.tenant_id, template=template, signers=[{"name": "Jane", "email": "jane@x.com"}]
    )
    client = APIClient()
    resp = client.get(f"/api/sign/requests/public/{req.token}")
    assert resp.status_code == 200
    assert resp.data["request"]["status"] == "Viewed"
    assert resp.data["template"]["name"] == "NDA"

    req.refresh_from_db()
    assert req.status == "Viewed"
    assert req.viewed_at is not None


@pytest.mark.django_db
def test_public_detail_unknown_token_404(db):
    client = APIClient()
    resp = client.get("/api/sign/requests/public/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_public_sign_completes_request(template):
    req = SignRequest.objects.create(
        tenant_id=template.tenant_id, template=template, signers=[{"name": "Jane", "email": "jane@x.com"}]
    )
    client = APIClient()
    resp = client.post(
        f"/api/sign/requests/public/{req.token}/sign",
        {"signature": "data:image/png;base64,fakebytes", "dateSigned": "2020-01-01T00:00:00Z"},
        format="json",
    )
    assert resp.status_code == 200
    req.refresh_from_db()
    assert req.status == "Signed"
    assert req.signature == "data:image/png;base64,fakebytes"
    assert req.signed_at is not None
    # server time, not the client-supplied dateSigned
    assert req.signed_at.year != 2020


@pytest.mark.django_db
def test_public_sign_rejects_already_signed(template):
    req = SignRequest.objects.create(
        tenant_id=template.tenant_id,
        template=template,
        signers=[{"name": "Jane", "email": "jane@x.com"}],
        status="Signed",
    )
    client = APIClient()
    resp = client.post(
        f"/api/sign/requests/public/{req.token}/sign",
        {"signature": "x"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_public_sign_requires_signature(template):
    req = SignRequest.objects.create(
        tenant_id=template.tenant_id, template=template, signers=[{"name": "Jane", "email": "jane@x.com"}]
    )
    client = APIClient()
    resp = client.post(f"/api/sign/requests/public/{req.token}/sign", {}, format="json")
    assert resp.status_code == 400
