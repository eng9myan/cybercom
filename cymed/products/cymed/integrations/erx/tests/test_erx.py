import json
import uuid
from decimal import Decimal

import httpx
import pytest
from rest_framework.test import APIClient

from products.cymed.integrations.erx import transport
from products.cymed.integrations.erx.models import ErxTransmission


def _client(mint_token, tenant, roles=("physician",)):
    c = APIClient()
    tok = mint_token({"sub": str(uuid.uuid4()), "email": "dr@x.io", "tenant_id": str(tenant),
                      "realm_access": {"roles": list(roles)}, "roles": list(roles)})
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}", HTTP_X_TENANT_ID=str(tenant))
    return c


def _rx(tenant, **kw):
    from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionItem

    defaults = dict(prescription_number=f"RX-{uuid.uuid4().hex[:8]}", patient_id=uuid.uuid4(),
                    prescriber_id=uuid.uuid4(), prescriber_npi="LIC-123", status="pending")
    defaults.update(kw)
    rx = Prescription.objects.create(tenant_id=tenant, **defaults)
    PrescriptionItem.objects.create(tenant_id=tenant, prescription=rx, drug_code="197361",
                                    drug_name="Amlodipine 5 mg tablet", dose="5", dose_unit="mg",
                                    route="oral", frequency="QD", quantity=Decimal("30"),
                                    quantity_unit="tablet", days_supply=30, sig="One tablet daily")
    return rx


def _send(client, rx, network="wasfaty"):
    return client.post("/api/v1/integrations/erx/transmit/",
                       {"prescription": str(rx.id), "network": network}, format="json")


@pytest.fixture
def fake_network(monkeypatch):
    """Point the wasfaty network at an in-process FHIR endpoint."""
    calls = []

    def install(status_code, body):
        def handler(request):
            calls.append(request)
            return httpx.Response(status_code, json=body)

        real_client = httpx.Client
        monkeypatch.setattr(transport.httpx, "Client",
                            lambda **kw: real_client(transport=httpx.MockTransport(handler)))
        monkeypatch.setenv("CYMED_ERX_WASFATY_URL", "https://erx.example/fhir/$process-message")
        monkeypatch.setenv("CYMED_ERX_WASFATY_TOKEN", "t0k")
        return calls

    return install


@pytest.mark.django_db
def test_unconfigured_network_is_reported_honestly(mint_token, mock_jwks, monkeypatch):
    monkeypatch.delenv("CYMED_ERX_WASFATY_URL", raising=False)
    t = uuid.uuid4()
    rx = _rx(t)
    resp = _send(_client(mint_token, t), rx)
    assert resp.status_code == 503
    assert resp.data["status"] == "not_configured"
    rx.refresh_from_db()
    assert rx.status == "pending"  # nothing pretended


@pytest.mark.django_db
def test_accepted_transmission_activates_prescription(mint_token, mock_jwks, fake_network):
    calls = fake_network(200, {"resourceType": "Bundle", "id": "ext-42"})
    t = uuid.uuid4()
    rx = _rx(t)
    resp = _send(_client(mint_token, t), rx)
    assert resp.status_code == 201, resp.data
    assert resp.data["external_id"] == "ext-42"
    sent = calls[0]
    assert sent.headers["Authorization"] == "Bearer t0k"
    bundle = json.loads(sent.content)
    med = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "MedicationRequest"]
    assert med[0]["medicationCodeableConcept"]["coding"][0]["code"] == "197361"
    assert med[0]["subject"]["reference"] == f"Patient/{rx.patient_id}"
    rx.refresh_from_db()
    assert rx.status == "active"


@pytest.mark.django_db
def test_network_rejection_carries_operation_outcome(mint_token, mock_jwks, fake_network):
    fake_network(422, {"resourceType": "OperationOutcome",
                       "issue": [{"severity": "error", "code": "invalid", "diagnostics": "Unknown drug code"}]})
    t = uuid.uuid4()
    resp = _send(_client(mint_token, t), _rx(t))
    assert resp.data["status"] == "rejected" and resp.data["detail"] == "Unknown drug code"


@pytest.mark.django_db
def test_controlled_rules_block_before_sending(mint_token, mock_jwks, fake_network):
    calls = fake_network(200, {"id": "x"})
    t = uuid.uuid4()
    c = _client(mint_token, t)
    no_reg = _send(c, _rx(t, is_controlled=True, dea_schedule="II"))
    assert no_reg.status_code == 422 and "registration is missing" in no_reg.data["detail"]
    refills = _send(c, _rx(t, is_controlled=True, dea_schedule="II", prescriber_dea="REG-9",
                           refills_authorized=2))
    assert "cannot authorise refills" in refills.data["detail"]
    assert calls == []  # nothing left the building


@pytest.mark.django_db
def test_pdmp_required_gates_controlled_prescriptions(mint_token, mock_jwks, fake_network, monkeypatch):
    fake_network(200, {"id": "x"})
    monkeypatch.setenv("CYMED_PDMP_REQUIRED", "1")
    monkeypatch.delenv("CYMED_PDMP_URL", raising=False)
    t = uuid.uuid4()
    c = _client(mint_token, t)
    rx = _rx(t, is_controlled=True, dea_schedule="IV", prescriber_dea="REG-9")
    assert "PDMP check is required" in _send(c, rx).data["detail"]
    check = c.post("/api/v1/integrations/erx/pdmp-checks/", {"prescription": str(rx.id)}, format="json")
    assert check.data["result"] == "not_configured"
    assert _send(c, rx).data["status"] == "blocked"  # not_configured never counts as a check


@pytest.mark.django_db
def test_other_tenants_prescription_is_not_found(mint_token, mock_jwks):
    rx = _rx(uuid.uuid4())
    resp = _send(_client(mint_token, uuid.uuid4()), rx)
    assert resp.status_code == 404
    assert not ErxTransmission.objects.exists()
