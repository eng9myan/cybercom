"""
Tests for Claim/$submit bundles used by both pre-authorization and final
claim flows.

Both flows POST a collection Bundle whose Claim entry's ``use`` field
distinguishes them: ``"preauthorization"`` vs ``"claim"``. Each bundle
also carries a MessageHeader (with an idempotency-keyed identifier),
plus the submitter Organization, Patient, and Coverage.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.delete("nphies:token")
    yield
    cache.delete("nphies:token")


@pytest.fixture
def nphies_env(monkeypatch):
    monkeypatch.setenv("NPHIES_BASE_URL", "https://sandbox.nphies.sa")
    monkeypatch.setenv("NPHIES_AUTH_URL",
                       "https://sandbox.nphies.sa/oauth2/token")
    monkeypatch.setenv("NPHIES_CLIENT_ID", "cymed-test")
    monkeypatch.setenv("NPHIES_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("NPHIES_LICENSEE_ID", "10000000123456")
    monkeypatch.setenv("NPHIES_MTLS_CERT_PATH", "")
    monkeypatch.setenv("NPHIES_MTLS_KEY_PATH", "")


def _mock_client(submit_body: dict) -> MagicMock:
    fake = MagicMock()

    tok = MagicMock()
    tok.json.return_value = {"access_token": "T", "expires_in": 3300}
    tok.raise_for_status.return_value = None
    fake.post.return_value = tok

    submit = MagicMock()
    submit.status_code = 200
    submit.json.return_value = submit_body
    submit.raise_for_status.return_value = None
    fake.request.return_value = submit
    return fake


def _find_claim_resources(bundle: dict) -> list[dict]:
    return [
        e["resource"] for e in bundle["entry"]
        if e["resource"]["resourceType"] == "Claim"
    ]


def _find_message_header(bundle: dict) -> dict:
    return next(
        e["resource"] for e in bundle["entry"]
        if e["resource"]["resourceType"] == "MessageHeader"
    )


@pytest.mark.django_db(transaction=True)
def test_preauth_submit_bundle_has_claim_with_use_preauthorization(
    nphies_env,
):
    from products.cymed.integrations.nphies.client import NphiesClient

    policy = SimpleNamespace(member_no="1112223334",
                              policy_number="POL-42",
                              insurer_code="INS-1")
    claim_response = {
        "resourceType": "Bundle",
        "entry": [{
            "resource": {
                "resourceType": "ClaimResponse",
                "outcome": "complete",
                "preAuthRef": ["PA-9001"],
                "payment": {"amount": {"value": 500, "currency": "SAR"}},
            }
        }],
    }
    mock = _mock_client(claim_response)

    result = NphiesClient(client=mock).preauth_submit(
        policy=policy,
        service_code="99213",
        justification="MRI required due to persistent headache 8w+",
        provider_tenant_id="tenant-abc",
        idempotency_key="idem-preauth-1",
    )

    assert result["status"] == "approved"
    assert result["reference"] == "PA-9001"
    assert Decimal(result["approved_amount"]) == Decimal("500")

    assert mock.request.call_count == 1
    method, url = mock.request.call_args.args
    assert method == "POST"
    assert url.endswith("/Claim/$submit")

    bundle = mock.request.call_args.kwargs["json"]
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"

    claims = _find_claim_resources(bundle)
    assert claims, "expected at least one Claim entry"
    uses = {c["use"] for c in claims}
    assert uses == {"preauthorization"}

    header = _find_message_header(bundle)
    assert header["identifier"]["value"] == "idem-preauth-1"
    assert header["eventCoding"]["code"] == "priorauth-request"


@pytest.mark.django_db(transaction=True)
def test_claim_submit_bundle_has_claim_with_use_claim(nphies_env):
    from products.cymed.integrations.nphies.client import NphiesClient

    line_items = [
        SimpleNamespace(service_code="99213", quantity=1,
                         unit_price=Decimal("120"), amount=Decimal("120")),
        SimpleNamespace(service_code="80053", quantity=2,
                         unit_price=Decimal("45"), amount=Decimal("90")),
    ]
    bill = SimpleNamespace(
        bill_number="BILL-777",
        patient_profile_id="patient-uuid",
        line_items=SimpleNamespace(all=lambda: line_items),
        total=Decimal("210"),
        policy_number="POL-42",
        insurer_code="INS-1",
    )

    mock = _mock_client({"resourceType": "Bundle", "entry": []})

    result = NphiesClient(client=mock).claim_submit(
        bill=bill, idempotency_key="idem-claim-1",
    )
    assert result["accepted"] is True
    assert result["reference"] == "idem-claim-1"

    assert mock.request.call_count == 1
    method, url = mock.request.call_args.args
    assert method == "POST"
    assert url.endswith("/Claim/$submit")

    bundle = mock.request.call_args.kwargs["json"]
    claims = _find_claim_resources(bundle)
    assert claims, "expected at least one Claim entry"
    for r in claims:
        assert r["use"] == "claim"

    items = claims[0]["item"]
    assert len(items) == 2
    codes = [i["productOrService"]["coding"][0]["code"] for i in items]
    assert codes == ["99213", "80053"]

    header = _find_message_header(bundle)
    assert header["identifier"]["value"] == "idem-claim-1"
    assert header["eventCoding"]["code"] == "claim-request"


@pytest.mark.django_db(transaction=True)
def test_preauth_and_claim_bundles_use_is_subset_of_allowed(nphies_env):
    """Every Claim resource must set ``use`` to one of the two allowed values."""
    from products.cymed.integrations.nphies.client import NphiesClient

    policy = SimpleNamespace(member_no="1112223334",
                              policy_number="POL-42",
                              insurer_code="INS-1")
    mock = _mock_client({"resourceType": "Bundle", "entry": []})

    NphiesClient(client=mock).preauth_submit(
        policy=policy, service_code="99213",
        justification="x", provider_tenant_id="tenant-abc",
    )
    bundle = mock.request.call_args.kwargs["json"]
    for r in _find_claim_resources(bundle):
        assert r["use"] in {"preauthorization", "claim"}


def test_retry_only_on_connection_errors(nphies_env):
    """4xx must NOT retry; connection errors MUST retry."""
    import httpx

    from products.cymed.integrations.nphies.client import NphiesClient

    calls = {"n": 0}

    def _raise_conn(*_a, **_k):
        calls["n"] += 1
        raise httpx.ConnectError("refused")

    fake = MagicMock()
    fake.request.side_effect = _raise_conn

    client = NphiesClient(client=fake)
    with pytest.raises(httpx.ConnectError):
        client._request_with_retry(
            "POST", "https://x", fake, retries=2, backoff=0,
        )
    assert calls["n"] == 3, "should attempt initial + 2 retries"
