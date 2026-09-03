"""Prior-authorization orchestrator — submits + polls + logs."""
from __future__ import annotations

from django.utils import timezone


class PreAuthOrchestrator:
    """Wraps the payments.services preauth flow and adds RCM audit."""

    def submit(self, *, policy_id, service_code: str, justification: str,
               provider_tenant_id) -> dict:
        try:
            from products.cymed.payments.services import submit_preauth
        except ImportError:
            return {"status": "denied", "error": "payments app unavailable"}
        preauth = submit_preauth(policy_id, service_code, justification, provider_tenant_id)
        return {
            "id": str(preauth.id),
            "status": preauth.status,
            "reference": preauth.reference_number,
            "approved_amount": str(preauth.approved_amount) if preauth.approved_amount else None,
        }

    def poll(self, *, preauth_id) -> dict:
        try:
            from products.cymed.payments.models import PreAuthorization
            from products.cymed.payments.insurers import get_insurer
        except ImportError:
            return {"status": "pending"}
        try:
            preauth = PreAuthorization.objects.get(id=preauth_id)
        except PreAuthorization.DoesNotExist:
            return {"status": "not_found"}
        insurer = get_insurer(preauth.policy.insurer_code)
        r = insurer.preauth_status(preauth.reference_number)
        preauth.status = r.status
        if r.approved_amount:
            preauth.approved_amount = r.approved_amount
        if r.status == "approved":
            preauth.approved_at = timezone.now()
        preauth.raw_response = r.raw
        preauth.save(update_fields=["status", "approved_amount", "approved_at",
                                      "raw_response", "updated_at"])
        return {"status": preauth.status,
                "approved_amount": str(preauth.approved_amount) if preauth.approved_amount else None}
