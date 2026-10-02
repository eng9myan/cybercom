"""NFC card scans require a staff token AND a registered terminal of the
caller's tenant AND the card's signature (2026-10-02 audit: was AllowAny)."""
import base64
import uuid
from datetime import date

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.utils import timezone
from rest_framework.test import APIClient

from platform.common.tenant_context import tenant_context
from products.cymed.patient_portal.models import NFCCard, NFCScanLog, PatientPortalProfile, ScanTerminal


def _client(mint_token, tenant, roles=("nurse",), terminal_key=None):
    c = APIClient()
    tok = mint_token({"sub": str(uuid.uuid4()), "email": "n@x.io", "tenant_id": str(tenant),
                      "realm_access": {"roles": list(roles)}, "roles": list(roles)})
    headers = {"HTTP_AUTHORIZATION": f"Bearer {tok}", "HTTP_X_TENANT_ID": str(tenant)}
    if terminal_key:
        headers["HTTP_X_TERMINAL_KEY"] = terminal_key
    c.credentials(**headers)
    return c


@pytest.fixture
def card():
    from products.cymed.core.patients.models import Patient

    home = uuid.uuid4()
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    with tenant_context(home):
        patient = Patient.objects.create(tenant_id=home, first_name="Card", last_name="Holder",
                                         dob=date(1980, 5, 5), mrn=f"MRN-{uuid.uuid4().hex[:8]}")
        profile = PatientPortalProfile.objects.create(tenant_id=home, patient=patient, user_id=uuid.uuid4())
        c = NFCCard.objects.create(tenant_id=home, profile=profile, public_key_pem=pem,
                                   activated_at=timezone.now())
    return c, key


def _register(mint_token, tenant):
    resp = _client(mint_token, tenant).post(
        "/api/v1/patient-portal/nfc/terminals/", {"terminal_id": "ER-1", "name": "ER desk"}, format="json")
    assert resp.status_code == 201, resp.data
    return f"ER-1:{resp.data['terminal_key']}"


def _challenge(client, card_obj):
    return client.post("/api/v1/patient-portal/nfc/challenge/",
                       {"card_uuid": str(card_obj.card_uuid)}, format="json")


@pytest.mark.django_db
def test_registered_terminal_can_scan(mint_token, mock_jwks, card):
    card_obj, key = card
    provider = uuid.uuid4()
    client = _client(mint_token, provider, terminal_key=_register(mint_token, provider))
    nonce = _challenge(client, card_obj).data["nonce"]
    sig = key.sign(base64.b64decode(nonce), ec.ECDSA(hashes.SHA256()))
    resp = client.post("/api/v1/patient-portal/nfc/scan/", {
        "card_uuid": str(card_obj.card_uuid), "nonce": nonce,
        "signature": base64.b64encode(sig).decode(), "purpose": "emergency",
    }, format="json")
    assert resp.status_code == 200, resp.data
    assert NFCScanLog.objects.get(card=card_obj).terminal_id == f"{provider}:ER-1"


@pytest.mark.django_db
def test_key_is_returned_once_and_stored_hashed(mint_token, mock_jwks):
    provider = uuid.uuid4()
    raw = _register(mint_token, provider).split(":", 1)[1]
    listed = _client(mint_token, provider).get("/api/v1/patient-portal/nfc/terminals/").data
    rows = listed.get("results", listed)
    assert "terminal_key" not in rows[0] and "key_hash" not in rows[0]
    assert ScanTerminal.objects.get(terminal_id="ER-1").key_hash != raw


@pytest.mark.django_db
def test_challenge_without_terminal_is_refused(mint_token, mock_jwks, card):
    card_obj, _ = card
    assert _challenge(_client(mint_token, uuid.uuid4()), card_obj).status_code == 401


@pytest.mark.django_db
def test_wrong_key_or_other_tenants_terminal_is_refused(mint_token, mock_jwks, card):
    card_obj, _ = card
    provider, other = uuid.uuid4(), uuid.uuid4()
    terminal_key = _register(mint_token, provider)
    wrong = _client(mint_token, provider, terminal_key="ER-1:not-the-key")
    assert _challenge(wrong, card_obj).status_code == 401
    borrowed = _client(mint_token, other, terminal_key=terminal_key)
    assert _challenge(borrowed, card_obj).status_code == 401


@pytest.mark.django_db
def test_patient_token_cannot_scan(mint_token, mock_jwks, card):
    card_obj, _ = card
    patient = _client(mint_token, uuid.uuid4(), roles=("patient",))
    assert _challenge(patient, card_obj).status_code == 403
