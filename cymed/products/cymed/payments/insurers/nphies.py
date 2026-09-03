"""NPHIES adapter — Saudi National Platform for Health Information Exchange.

Uses FHIR-based Coverage / CoverageEligibilityRequest / Claim resources.
Live implementation calls the NPHIES FHIR server; this stub demonstrates the
control flow and returns realistic shapes so downstream code can rely on it.
Real client lives in P0-3 `products.cymed.integrations.nphies`.
"""
import os
from decimal import Decimal
from uuid import UUID

from .base import BaseInsurer, ClaimResult, EligibilityResult, PreAuthResult


class NphiesInsurer(BaseInsurer):
    code = "NPHIES"
    country = "SA"

    def __init__(self):
        self.base = os.environ.get("NPHIES_BASE_URL", "https://sandbox.nphies.sa/fhir/R4")
        self.client_id = os.environ.get("NPHIES_CLIENT_ID", "")
        self.client_secret = os.environ.get("NPHIES_CLIENT_SECRET", "")

    # Real client comes from P0-3 integration module
    def _client(self):
        try:
            from products.cymed.integrations.nphies.client import NphiesClient
            return NphiesClient()
        except ImportError:
            return None

    def eligibility(self, policy, service_code, provider_tenant_id: UUID | None = None):
        client = self._client()
        if client is None:
            return EligibilityResult(covered=False,
                                      raw={"error": "NPHIES client not yet available"})
        resp = client.coverage_eligibility_request(
            insurer=policy.insurer_code,
            policy_number=policy.policy_number,
            member_no=policy.member_no,
            service_code=service_code,
            provider_tenant_id=str(provider_tenant_id) if provider_tenant_id else "",
        )
        return EligibilityResult(
            covered=bool(resp.get("covered", False)),
            co_pay_amount=Decimal(str(resp.get("co_pay_amount", "0"))) if resp.get("co_pay_amount") is not None else None,
            co_pay_percent=Decimal(str(resp.get("co_pay_percent", "0"))) if resp.get("co_pay_percent") is not None else None,
            requires_preauth=bool(resp.get("requires_preauth", False)),
            patient_responsibility=Decimal(str(resp.get("patient_responsibility", "0"))) if resp.get("patient_responsibility") is not None else None,
            raw=resp,
        )

    def preauth_submit(self, policy, service_code, justification, provider_tenant_id: UUID):
        client = self._client()
        if client is None:
            return PreAuthResult(status="pending", raw={"error": "NPHIES client unavailable"})
        resp = client.preauth_submit(policy=policy, service_code=service_code,
                                      justification=justification,
                                      provider_tenant_id=str(provider_tenant_id))
        return PreAuthResult(
            status=resp.get("status", "pending"),
            reference_number=resp.get("reference", ""),
            approved_amount=Decimal(str(resp["approved_amount"])) if resp.get("approved_amount") else None,
            raw=resp,
        )

    def preauth_status(self, reference):
        client = self._client()
        if client is None:
            return PreAuthResult(status="pending", reference_number=reference)
        resp = client.preauth_status(reference)
        return PreAuthResult(
            status=resp.get("status", "pending"),
            reference_number=reference,
            approved_amount=Decimal(str(resp["approved_amount"])) if resp.get("approved_amount") else None,
            raw=resp,
        )

    def claim_submit(self, bill):
        client = self._client()
        if client is None:
            return ClaimResult(accepted=False, raw={"error": "NPHIES client unavailable"})
        resp = client.claim_submit(bill=bill)
        return ClaimResult(
            accepted=bool(resp.get("accepted", False)),
            reference_number=resp.get("reference", ""),
            denial_reason=resp.get("denial_reason", ""),
            raw=resp,
        )
