"""
NPHIES FHIR R4 client — sandbox-capable, mTLS-hardened.

The Saudi National Platform for Health Information Exchange Services
(NPHIES) exposes a set of FHIR R4 operations for eligibility, prior
authorisation, claim submission, and remittance. This module implements
the five core transactions with real network semantics:

* OAuth2 ``client_credentials`` against ``/oauth2/token`` (token cached
  in :mod:`django.core.cache` for ``expires_in - 60`` seconds).
* Mutual TLS on every non-token endpoint via ``httpx.Client(cert=(cert, key))``.
* FHIR Bundles of ``type=collection`` carrying a ``MessageHeader``,
  the domain resource (CoverageEligibilityRequest / Claim), and the
  supporting Organization / Patient / Coverage resources — all stamped
  with the KSA NPHIES profile URIs under
  ``http://nphies.sa/fhir/ksa/nphies-fs``.
* Optional caller-supplied ``idempotency_key`` that becomes the
  ``MessageHeader.identifier.value`` so NPHIES will reject duplicate
  submissions instead of double-processing them.
* Retry with exponential backoff, but **only** on connection-level
  errors — a real 4xx from NPHIES is propagated to the caller.

Environment variables read (all optional; sandbox defaults where safe)::

    NPHIES_BASE_URL          default https://sandbox.nphies.sa
    NPHIES_AUTH_URL          default {NPHIES_BASE_URL}/oauth2/token
    NPHIES_CLIENT_ID         OAuth2 client id (from payer onboarding)
    NPHIES_CLIENT_SECRET     OAuth2 client secret
    NPHIES_SCOPES            space-separated scopes (default: "nphies")
    NPHIES_MTLS_CERT_PATH    path to PEM client cert
    NPHIES_MTLS_KEY_PATH     path to PEM client key
    NPHIES_LICENSEE_ID       CCHI provider license id (baked into
                             Organization.identifier)

NPHIES documents move quickly; leave every URL configurable via env.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from decimal import Decimal
from typing import Any

import httpx
from django.core.cache import cache
from django.utils import timezone

from .models import NphiesInteraction


logger = logging.getLogger("cymed.integrations.nphies")

# ── FHIR profile URIs ───────────────────────────────────────────────────
PROFILE_BASE = "http://nphies.sa/fhir/ksa/nphies-fs"
PROFILE_SD = f"{PROFILE_BASE}/StructureDefinition"

TOKEN_CACHE_KEY = "nphies:token"
DEFAULT_TIMEOUT = 45
DEFAULT_SANDBOX_BASE = "https://sandbox.nphies.sa"


# ── Module-level helpers (small, testable, injectable) ─────────────────
def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _sandbox_base_url() -> str:
    return _env("NPHIES_BASE_URL", DEFAULT_SANDBOX_BASE).rstrip("/")


def build_mtls_client(cert_path: str, key_path: str,
                      *, timeout: int = DEFAULT_TIMEOUT) -> httpx.Client:
    """Build an ``httpx.Client`` configured for NPHIES mTLS.

    Raises ``RuntimeError`` if either the cert or key path is empty —
    NPHIES rejects plain TLS on all FHIR endpoints.
    """
    if not (cert_path and key_path):
        raise RuntimeError(
            "NPHIES mTLS not configured: set NPHIES_MTLS_CERT_PATH and "
            "NPHIES_MTLS_KEY_PATH. NPHIES requires client certificates "
            "for every non-token endpoint."
        )
    return httpx.Client(
        cert=(cert_path, key_path),
        verify=True,
        timeout=timeout,
    )


# ── Client ─────────────────────────────────────────────────────────────
class NphiesClient:
    """Injectable NPHIES FHIR client.

    Pass ``client=<httpx.Client>`` to reuse a session (recommended in
    long-running processes) or to inject a mock in tests. If omitted a
    fresh mTLS ``httpx.Client`` is built per FHIR call and closed
    afterwards.
    """

    def __init__(self, client: httpx.Client | None = None):
        self.base_url = _sandbox_base_url()
        self.auth_url = _env(
            "NPHIES_AUTH_URL", f"{self.base_url}/oauth2/token"
        )
        self.client_id = _env("NPHIES_CLIENT_ID")
        self.client_secret = _env("NPHIES_CLIENT_SECRET")
        self.scopes = _env("NPHIES_SCOPES", "nphies")
        self.licensee_id = _env("NPHIES_LICENSEE_ID")
        self.mtls_cert = _env("NPHIES_MTLS_CERT_PATH")
        self.mtls_key = _env("NPHIES_MTLS_KEY_PATH")
        self._injected_client = client

    # ── Client management ─────────────────────────────────────────────
    def _acquire_client(self) -> tuple[httpx.Client, bool]:
        """Return ``(client, must_close)``.

        If the caller injected a client we reuse it and never close it.
        Otherwise we build a fresh mTLS client that the caller is
        responsible for closing.
        """
        if self._injected_client is not None:
            return self._injected_client, False
        return build_mtls_client(self.mtls_cert, self.mtls_key), True

    # ── Auth (OAuth2 client_credentials) ──────────────────────────────
    def _token(self) -> str:
        cached = cache.get(TOKEN_CACHE_KEY)
        if cached:
            return cached
        return self._fetch_token()

    def _fetch_token(self) -> str:
        """POST ``/oauth2/token`` and cache the access token."""
        data: dict[str, str] = {"grant_type": "client_credentials"}
        if self.scopes:
            data["scope"] = self.scopes
        auth = (self.client_id, self.client_secret)

        logger.info(
            "nphies.token.request",
            extra={"url": self.auth_url, "scopes": self.scopes},
        )

        # The token endpoint may or may not require mTLS depending on
        # the NPHIES tenancy — supply it when configured so both work.
        client_kwargs: dict[str, Any] = {
            "timeout": DEFAULT_TIMEOUT,
            "verify": True,
        }
        if self.mtls_cert and self.mtls_key:
            client_kwargs["cert"] = (self.mtls_cert, self.mtls_key)

        # If the caller injected a client we reuse it (tests exercise
        # this path); otherwise we build a fresh one just for the token
        # exchange.
        if self._injected_client is not None:
            r = self._injected_client.post(self.auth_url, data=data, auth=auth)
        else:
            with httpx.Client(**client_kwargs) as c:
                r = c.post(self.auth_url, data=data, auth=auth)
        r.raise_for_status()
        body = r.json()
        token = body["access_token"]
        ttl = int(body.get("expires_in", 3600)) - 60
        cache.set(TOKEN_CACHE_KEY, token, ttl)
        logger.info(
            "nphies.token.cached",
            extra={"ttl_seconds": ttl, "token_type": body.get("token_type")},
        )
        return token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token()}",
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        }

    # ── Transport ─────────────────────────────────────────────────────
    def _post(self, path: str, bundle: dict) -> dict:
        url = f"{self.base_url}{path}"
        headers = self._headers()
        client, must_close = self._acquire_client()
        try:
            r = self._request_with_retry(
                "POST", url, client, json=bundle, headers=headers
            )
            r.raise_for_status()
            return r.json()
        finally:
            if must_close:
                client.close()

    def _get(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        headers = self._headers()
        client, must_close = self._acquire_client()
        try:
            r = self._request_with_retry(
                "GET", url, client, headers=headers
            )
            r.raise_for_status()
            return r.json()
        finally:
            if must_close:
                client.close()

    @staticmethod
    def _request_with_retry(method: str, url: str, client: httpx.Client,
                            *, retries: int = 2, backoff: float = 0.5,
                            **kwargs: Any) -> httpx.Response:
        """Retry ONLY on connection-level errors.

        4xx and 5xx status codes are returned as-is so the caller can
        decide how to react (a 400 from NPHIES is a data problem, not a
        transport blip). We back off exponentially before each retry.
        """
        connection_errors: tuple[type[BaseException], ...] = (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
            httpx.NetworkError,
        )
        attempt = 0
        while True:
            try:
                logger.debug(
                    "nphies.http.request",
                    extra={"method": method, "url": url, "attempt": attempt},
                )
                return client.request(method, url, **kwargs)
            except connection_errors as exc:
                if attempt >= retries:
                    logger.error(
                        "nphies.http.retry_exhausted",
                        extra={
                            "url": url,
                            "attempts": attempt + 1,
                            "error": str(exc),
                        },
                    )
                    raise
                sleep_for = backoff * (2 ** attempt)
                logger.warning(
                    "nphies.http.retrying",
                    extra={
                        "url": url,
                        "attempt": attempt,
                        "sleep_s": sleep_for,
                        "error": str(exc),
                    },
                )
                time.sleep(sleep_for)
                attempt += 1

    # ── FHIR resource builders ────────────────────────────────────────
    def _message_header(self, *, event_code: str, focus_refs: list[str],
                        idempotency_key: str,
                        destination_endpoint: str) -> dict:
        """Build a MessageHeader with ``identifier.value = idempotency_key``.

        NPHIES uses the MessageHeader.identifier to de-duplicate
        submissions — passing a stable ``idempotency_key`` lets the
        caller safely retry without double-processing.
        """
        return {
            "resourceType": "MessageHeader",
            "id": str(uuid.uuid4()),
            "meta": {"profile": [f"{PROFILE_SD}/message-header"]},
            "eventCoding": {
                "system": f"{PROFILE_BASE}/CodeSystem/ksa-message-events",
                "code": event_code,
            },
            "destination": [{
                "endpoint": destination_endpoint,
                "receiver": {"identifier": {"value": "nphies"}},
            }],
            "source": {"endpoint": "http://cymed.local/nphies"},
            "sender": {"identifier": {"value": self.licensee_id}},
            "focus": [{"reference": ref} for ref in focus_refs],
            "identifier": {"value": idempotency_key},
        }

    def _submitter_organization(self) -> dict:
        return {
            "resourceType": "Organization",
            "id": self.licensee_id or "provider",
            "meta": {"profile": [f"{PROFILE_SD}/provider-organization"]},
            "identifier": [{
                "system": "http://nphies.sa/license/provider-license",
                "value": self.licensee_id,
            }],
            "active": True,
            "type": [{
                "coding": [{
                    "system": (
                        "http://nphies.sa/terminology/CodeSystem/"
                        "organization-type"
                    ),
                    "code": "prov",
                }],
            }],
        }

    def _patient(self, member_no: str) -> dict:
        return {
            "resourceType": "Patient",
            "id": member_no,
            "meta": {"profile": [f"{PROFILE_SD}/patient"]},
            "identifier": [{
                "system": "http://nphies.sa/identifier/iqama",
                "value": member_no,
            }],
        }

    def _coverage(self, *, policy_number: str, insurer: str,
                  member_no: str) -> dict:
        return {
            "resourceType": "Coverage",
            "id": policy_number or "coverage",
            "meta": {"profile": [f"{PROFILE_SD}/coverage"]},
            "identifier": [{
                "system": "http://nphies.sa/identifier/memberid",
                "value": policy_number,
            }],
            "status": "active",
            "beneficiary": {"reference": f"Patient/{member_no}"},
            "payor": [{"identifier": {"value": insurer}}],
        }

    # ── Coverage Eligibility ──────────────────────────────────────────
    def coverage_eligibility_request(self, *, insurer: str,
                                     policy_number: str,
                                     member_no: str, service_code: str,
                                     provider_tenant_id: str,
                                     idempotency_key: str | None = None
                                     ) -> dict:
        """Submit a CoverageEligibilityRequest bundle to NPHIES."""
        start = time.time()
        correlation = idempotency_key or str(uuid.uuid4())
        bundle = self._build_eligibility_bundle(
            correlation=correlation,
            insurer=insurer,
            policy_number=policy_number,
            member_no=member_no,
            service_code=service_code,
            provider_tenant_id=provider_tenant_id,
        )
        interaction = NphiesInteraction.objects.create(
            kind="eligibility", status="sent",
            licensee_id=self.licensee_id, correlation_id=correlation,
            request_bundle=bundle,
        )
        logger.info(
            "nphies.eligibility.submit",
            extra={"correlation_id": correlation, "insurer": insurer,
                   "service_code": service_code},
        )
        try:
            resp = self._post("/CoverageEligibilityRequest/$submit", bundle)
            interaction.status = "succeeded"
            interaction.response_bundle = resp
            interaction.duration_ms = int((time.time() - start) * 1000)
            interaction.save()
            return self._parse_eligibility_response(resp)
        except httpx.HTTPStatusError as exc:
            msg = f"{exc.response.status_code} {exc.response.text[:200]}"
            interaction.status = "failed"
            interaction.error_message = msg
            interaction.duration_ms = int((time.time() - start) * 1000)
            interaction.save()
            logger.error(
                "nphies.eligibility.failed",
                extra={"correlation_id": correlation,
                       "status": exc.response.status_code},
            )
            return {"covered": False, "error": msg}

    def _build_eligibility_bundle(self, **kw: Any) -> dict:
        correlation = kw["correlation"]
        member_no = kw["member_no"]
        policy_number = kw["policy_number"]
        insurer = kw["insurer"]
        service_code = kw["service_code"]

        header_uuid = f"urn:uuid:{uuid.uuid4()}"
        eligibility_uuid = f"urn:uuid:{uuid.uuid4()}"
        org_uuid = f"urn:uuid:{uuid.uuid4()}"
        patient_uuid = f"urn:uuid:{uuid.uuid4()}"
        coverage_uuid = f"urn:uuid:{uuid.uuid4()}"

        eligibility_resource = {
            "resourceType": "CoverageEligibilityRequest",
            "id": correlation,
            "meta": {"profile": [f"{PROFILE_SD}/eligibility-request"]},
            "identifier": [{"value": correlation}],
            "status": "active",
            "purpose": ["benefits"],
            "patient": {"reference": patient_uuid,
                         "identifier": {"value": member_no}},
            "created": timezone.now().isoformat(),
            "provider": {"reference": org_uuid,
                          "identifier": {"value": self.licensee_id}},
            "insurer": {"identifier": {"value": insurer}},
            "insurance": [{
                "coverage": {"reference": coverage_uuid,
                              "identifier": {"value": policy_number}},
            }],
            "item": [{"category": {"coding": [{"code": service_code}]}}],
        }

        destination = (
            f"{self.base_url}/CoverageEligibilityRequest/$submit"
        )
        return {
            "resourceType": "Bundle",
            "id": correlation,
            "type": "collection",
            "meta": {
                "profile": [f"{PROFILE_SD}/eligibility-request-bundle"]
            },
            "timestamp": timezone.now().isoformat(),
            "entry": [
                {
                    "fullUrl": header_uuid,
                    "resource": self._message_header(
                        event_code="eligibility-request",
                        focus_refs=[eligibility_uuid],
                        idempotency_key=correlation,
                        destination_endpoint=destination,
                    ),
                },
                {"fullUrl": eligibility_uuid,
                 "resource": eligibility_resource},
                {"fullUrl": org_uuid,
                 "resource": self._submitter_organization()},
                {"fullUrl": patient_uuid,
                 "resource": self._patient(member_no)},
                {"fullUrl": coverage_uuid,
                 "resource": self._coverage(
                     policy_number=policy_number,
                     insurer=insurer,
                     member_no=member_no,
                 )},
            ],
        }

    def _parse_eligibility_response(self, resp: dict) -> dict:
        for entry in resp.get("entry", []):
            r = entry.get("resource", {})
            if r.get("resourceType") == "CoverageEligibilityResponse":
                insurance = (r.get("insurance") or [{}])[0]
                items = insurance.get("item") or []
                item = items[0] if items else {}
                benefit = (item.get("benefit") or [{}])[0]
                return {
                    "covered": r.get("outcome") == "complete",
                    "co_pay_amount": None,
                    "co_pay_percent": None,
                    "requires_preauth": bool(item.get("authorizationRequired")),
                    "patient_responsibility": (
                        benefit.get("usedMoney", {}).get("value")
                    ),
                }
        return {"covered": False, "raw": resp}

    # ── Pre-Auth / Claim shared builder ───────────────────────────────
    def _build_claim_bundle(self, *, use: str, correlation: str,
                            member_no: str, policy_number: str,
                            insurer: str, items: list[dict],
                            supporting_info: list[dict] | None = None,
                            total: dict | None = None,
                            claim_identifier: str | None = None
                            ) -> dict:
        if use not in {"preauthorization", "claim"}:
            raise ValueError(f"claim use must be preauthorization|claim, got {use!r}")

        profile = (
            f"{PROFILE_SD}/priorauth"
            if use == "preauthorization"
            else f"{PROFILE_SD}/institutional-claim"
        )
        bundle_profile = (
            f"{PROFILE_SD}/priorauth-bundle"
            if use == "preauthorization"
            else f"{PROFILE_SD}/claim-bundle"
        )
        event_code = (
            "priorauth-request"
            if use == "preauthorization"
            else "claim-request"
        )

        header_uuid = f"urn:uuid:{uuid.uuid4()}"
        claim_uuid = f"urn:uuid:{uuid.uuid4()}"
        org_uuid = f"urn:uuid:{uuid.uuid4()}"
        patient_uuid = f"urn:uuid:{uuid.uuid4()}"
        coverage_uuid = f"urn:uuid:{uuid.uuid4()}"

        claim_resource: dict[str, Any] = {
            "resourceType": "Claim",
            "id": correlation,
            "meta": {"profile": [profile]},
            "identifier": [{"value": claim_identifier or correlation}],
            "status": "active",
            "type": {"coding": [{"code": "institutional"}]},
            "use": use,
            "patient": {"reference": patient_uuid,
                         "identifier": {"value": member_no}},
            "created": timezone.now().isoformat(),
            "provider": {"reference": org_uuid,
                          "identifier": {"value": self.licensee_id}},
            "insurance": [{
                "sequence": 1,
                "focal": True,
                "coverage": {"reference": coverage_uuid,
                              "identifier": {"value": policy_number}},
            }],
            "item": items,
        }
        if supporting_info:
            claim_resource["supportingInfo"] = supporting_info
        if total is not None:
            claim_resource["total"] = total

        destination = f"{self.base_url}/Claim/$submit"

        return {
            "resourceType": "Bundle",
            "id": correlation,
            "type": "collection",
            "meta": {"profile": [bundle_profile]},
            "timestamp": timezone.now().isoformat(),
            "entry": [
                {
                    "fullUrl": header_uuid,
                    "resource": self._message_header(
                        event_code=event_code,
                        focus_refs=[claim_uuid],
                        idempotency_key=correlation,
                        destination_endpoint=destination,
                    ),
                },
                {"fullUrl": claim_uuid, "resource": claim_resource},
                {"fullUrl": org_uuid,
                 "resource": self._submitter_organization()},
                {"fullUrl": patient_uuid,
                 "resource": self._patient(member_no)},
                {"fullUrl": coverage_uuid,
                 "resource": self._coverage(
                     policy_number=policy_number,
                     insurer=insurer,
                     member_no=member_no,
                 )},
            ],
        }

    # ── Pre-Auth ──────────────────────────────────────────────────────
    def preauth_submit(self, *, policy, service_code: str,
                       justification: str, provider_tenant_id: str,
                       idempotency_key: str | None = None) -> dict:
        start = time.time()
        correlation = idempotency_key or str(uuid.uuid4())
        insurer = getattr(policy, "insurer_code", "") or getattr(policy, "insurer", "")
        bundle = self._build_claim_bundle(
            use="preauthorization",
            correlation=correlation,
            member_no=policy.member_no,
            policy_number=policy.policy_number,
            insurer=insurer,
            items=[{
                "sequence": 1,
                "productOrService": {"coding": [{"code": service_code}]},
            }],
            supporting_info=[{
                "sequence": 1,
                "category": {"text": "clinical-justification"},
                "valueString": justification[:1000],
            }],
        )
        NphiesInteraction.objects.create(
            kind="preauth_submit", status="sent",
            correlation_id=correlation, request_bundle=bundle,
        )
        logger.info(
            "nphies.preauth.submit",
            extra={"correlation_id": correlation,
                   "service_code": service_code},
        )
        try:
            resp = self._post("/Claim/$submit", bundle)
            duration_ms = int((time.time() - start) * 1000)
            logger.info(
                "nphies.preauth.ok",
                extra={"correlation_id": correlation,
                       "duration_ms": duration_ms},
            )
            return self._parse_preauth_response(resp, correlation)
        except httpx.HTTPStatusError as exc:
            msg = f"{exc.response.status_code} {exc.response.text[:200]}"
            logger.error(
                "nphies.preauth.failed",
                extra={"correlation_id": correlation,
                       "status": exc.response.status_code},
            )
            return {"status": "denied", "error": msg}

    def preauth_status(self, reference: str) -> dict:
        try:
            body = self._get(f"/Task?identifier={reference}")
            for e in body.get("entry", []):
                t = e.get("resource", {})
                if t.get("resourceType") == "Task":
                    return {"status": t.get("status", "pending")}
        except httpx.HTTPStatusError as exc:
            return {"status": "pending",
                    "error": f"{exc.response.status_code}"}
        return {"status": "pending"}

    def _parse_preauth_response(self, resp: dict, correlation: str) -> dict:
        for entry in resp.get("entry", []):
            r = entry.get("resource", {})
            if r.get("resourceType") == "ClaimResponse":
                outcome = r.get("outcome")
                ref = (r.get("preAuthRef") or [None])[0]
                approved: Decimal | None = None
                if r.get("payment") and r["payment"].get("amount"):
                    approved = Decimal(
                        str(r["payment"]["amount"].get("value", 0))
                    )
                status = "approved" if outcome == "complete" else "denied"
                return {
                    "status": status,
                    "reference": ref or correlation,
                    "approved_amount": str(approved) if approved else None,
                }
        return {"status": "pending", "reference": correlation}

    # ── Claim submit ──────────────────────────────────────────────────
    def claim_submit(self, *, bill,
                     idempotency_key: str | None = None) -> dict:
        start = time.time()
        correlation = idempotency_key or str(uuid.uuid4())
        items: list[dict] = []
        for i, li in enumerate(bill.line_items.all(), start=1):
            items.append({
                "sequence": i,
                "productOrService": {
                    "coding": [{"code": li.service_code}]
                },
                "quantity": {"value": float(li.quantity)},
                "unitPrice": {"value": float(li.unit_price),
                               "currency": "SAR"},
                "net": {"value": float(li.amount), "currency": "SAR"},
            })
        insurer = getattr(bill, "insurer_code", "") or getattr(bill, "insurer", "")
        policy_number = getattr(bill, "policy_number", "") or "unknown"
        member_no = str(bill.patient_profile_id)
        bundle = self._build_claim_bundle(
            use="claim",
            correlation=correlation,
            member_no=member_no,
            policy_number=policy_number,
            insurer=insurer,
            items=items,
            total={"value": float(bill.total), "currency": "SAR"},
            claim_identifier=bill.bill_number,
        )
        NphiesInteraction.objects.create(
            kind="claim_submit", status="sent",
            correlation_id=correlation, request_bundle=bundle,
        )
        logger.info(
            "nphies.claim.submit",
            extra={"correlation_id": correlation,
                   "bill_number": bill.bill_number,
                   "item_count": len(items)},
        )
        try:
            resp = self._post("/Claim/$submit", bundle)
            duration_ms = int((time.time() - start) * 1000)
            logger.info(
                "nphies.claim.ok",
                extra={"correlation_id": correlation,
                       "duration_ms": duration_ms},
            )
            return {"accepted": True, "reference": correlation, "raw": resp}
        except httpx.HTTPStatusError as exc:
            msg = f"{exc.response.status_code} {exc.response.text[:200]}"
            logger.error(
                "nphies.claim.failed",
                extra={"correlation_id": correlation,
                       "status": exc.response.status_code},
            )
            return {"accepted": False, "denial_reason": msg}
