"""
Tests for CoverageEligibilityRequest bundle construction and submission.

Verifies that:

* the built FHIR Bundle carries the Saudi profile URI
  ``http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/eligibility-request``,
* the outer resource is a proper ``Bundle`` (``type=collection``) with a
  MessageHeader, CoverageEligibilityRequest, Organization, Patient, and
  Coverage entry, and
* the response parser reads coverage/authorization fields from the
  mocked network response.

External HTTP is fully mocked via an injected ``httpx.Client`` — no
real socket is opened.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from django.core.cache import cache

from platform.common.tenant_context import tenant_context


@pytest.fixture(autouse=True)
def _tenant_ctx():
    """NphiesInteraction (a tenant-scoped BaseModel) is written inside the
    client; in production the request/task sets the tenant context, so mirror
    that here rather than threading a tenant_id through the unit test."""
    with tenant_context(uuid.uuid4()):
        yield


PROFILE_URI = (
    "http://nphies.sa/fhir/ksa/nphies-fs/StructureDefinition/eligibility-request"
)


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


def _canned_eligibility_response() -> dict:
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "CoverageEligibilityResponse",
                    "outcome": "complete",
                    "insurance": [{
                        "item": [{
                            "authorizationRequired": True,
                            "benefit": [{
                                "usedMoney": {"value": 150, "currency": "SAR"},
                            }],
                        }],
                    }],
                }
            }
        ],
    }


def _mock_client(*, post_body: dict | None = None,
                  post_status: int = 200) -> MagicMock:
    """Injected httpx.Client mock: first .post() is token, then submit."""
    fake = MagicMock()

    token_resp = MagicMock()
    token_resp.json.return_value = {"access_token": "T",
                                     "expires_in": 3300}
    token_resp.raise_for_status.return_value = None

    submit_resp = MagicMock()
    submit_resp.status_code = post_status
    submit_resp.json.return_value = (
        post_body or _canned_eligibility_response()
    )
    if post_status >= 400:
        req = httpx.Request("POST", "https://sandbox.nphies.sa/x")
        submit_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "boom", request=req, response=httpx.Response(post_status, text="boom"),
        )
    else:
        submit_resp.raise_for_status.return_value = None

    fake.post.return_value = token_resp
    fake.request.return_value = submit_resp
    return fake


def test_build_eligibility_bundle_has_saudi_profile_uri(nphies_env):
    from products.cymed.integrations.nphies.client import NphiesClient

    bundle = NphiesClient()._build_eligibility_bundle(
        correlation="corr-1",
        insurer="INS-777",
        policy_number="POL-42",
        member_no="1112223334",
        service_code="99213",
        provider_tenant_id="tenant-abc",
    )

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection", (
        "NPHIES eligibility bundles are collection bundles carrying a "
        "MessageHeader plus the eligibility request"
    )

    resources_by_type = {
        e["resource"]["resourceType"]: e["resource"]
        for e in bundle["entry"]
    }
    assert "MessageHeader" in resources_by_type
    assert "CoverageEligibilityRequest" in resources_by_type
    assert "Organization" in resources_by_type
    assert "Patient" in resources_by_type
    assert "Coverage" in resources_by_type

    req = resources_by_type["CoverageEligibilityRequest"]
    assert PROFILE_URI in req["meta"]["profile"]
    assert req["patient"]["identifier"]["value"] == "1112223334"

    coverage = resources_by_type["Coverage"]
    assert coverage["identifier"][0]["value"] == "POL-42"

    header = resources_by_type["MessageHeader"]
    assert header["destination"][0]["endpoint"].endswith(
        "/CoverageEligibilityRequest/$submit"
    )


def test_idempotency_key_is_used_as_message_header_identifier(nphies_env):
    from products.cymed.integrations.nphies.client import NphiesClient

    bundle = NphiesClient()._build_eligibility_bundle(
        correlation="idem-42",
        insurer="INS-1", policy_number="POL-1", member_no="M1",
        service_code="99213", provider_tenant_id="t1",
    )
    header = next(
        e["resource"] for e in bundle["entry"]
        if e["resource"]["resourceType"] == "MessageHeader"
    )
    assert header["identifier"]["value"] == "idem-42"


@pytest.mark.django_db(transaction=True)
def test_coverage_eligibility_request_posts_bundle_and_parses_response(
    nphies_env,
):
    from products.cymed.integrations.nphies.client import NphiesClient
    from products.cymed.integrations.nphies.models import NphiesInteraction

    mock = _mock_client()

    result = NphiesClient(client=mock).coverage_eligibility_request(
        insurer="INS-777",
        policy_number="POL-42",
        member_no="1112223334",
        service_code="99213",
        provider_tenant_id="tenant-abc",
        idempotency_key="idem-xyz",
    )

    assert result["covered"] is True
    assert result["requires_preauth"] is True
    assert result["patient_responsibility"] == 150

    # Token exchange (post) + submit (request) both happened
    assert mock.post.call_count == 1
    assert mock.request.call_count == 1
    method, url = mock.request.call_args.args
    assert method == "POST"
    assert url.endswith("/CoverageEligibilityRequest/$submit")

    posted_bundle = mock.request.call_args.kwargs["json"]
    assert posted_bundle["resourceType"] == "Bundle"
    assert posted_bundle["type"] == "collection"

    resources = [e["resource"] for e in posted_bundle["entry"]]
    types = {r["resourceType"] for r in resources}
    assert {
        "MessageHeader", "CoverageEligibilityRequest",
        "Organization", "Patient", "Coverage",
    }.issubset(types)

    interaction = NphiesInteraction.objects.order_by("-created_at").first()
    assert interaction is not None
    assert interaction.kind == "eligibility"
    assert interaction.status == "succeeded"
    assert interaction.correlation_id == "idem-xyz"
    assert interaction.duration_ms is not None
    assert interaction.duration_ms >= 0


@pytest.mark.django_db(transaction=True)
def test_coverage_eligibility_request_records_failure_on_http_error(
    nphies_env,
):
    from products.cymed.integrations.nphies.client import NphiesClient
    from products.cymed.integrations.nphies.models import NphiesInteraction

    mock = _mock_client(post_status=500)

    result = NphiesClient(client=mock).coverage_eligibility_request(
        insurer="INS-777", policy_number="POL-42",
        member_no="1112223334", service_code="99213",
        provider_tenant_id="tenant-abc",
    )

    assert result["covered"] is False
    assert "500" in result["error"]

    interaction = NphiesInteraction.objects.order_by("-created_at").first()
    assert interaction is not None
    assert interaction.status == "failed"
    assert "500" in interaction.error_message
