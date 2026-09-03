"""Manual insurer — queues human review. Fallback for smaller insurers."""
from uuid import UUID

from .base import BaseInsurer, ClaimResult, EligibilityResult, PreAuthResult


class ManualInsurer(BaseInsurer):
    code = "MANUAL"
    country = "SA"

    def eligibility(self, policy, service_code, provider_tenant_id=None):
        # Optimistic default — no automated verification.
        return EligibilityResult(
            covered=True,
            co_pay_percent=policy.co_pay_percent,
            co_pay_amount=policy.co_pay_fixed,
            requires_preauth=service_code in (policy.pre_auth_required or []),
            raw={"note": "manual insurer — verify by phone"},
        )

    def preauth_submit(self, policy, service_code, justification, provider_tenant_id: UUID):
        return PreAuthResult(status="pending", reference_number="MANUAL",
                              raw={"note": "manual insurer — queue for staff"})

    def preauth_status(self, reference):
        return PreAuthResult(status="pending", reference_number=reference)

    def claim_submit(self, bill):
        return ClaimResult(accepted=False, reference_number="MANUAL",
                            raw={"note": "manual insurer — staff submits offline"})
