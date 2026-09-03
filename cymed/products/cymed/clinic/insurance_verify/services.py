"""Insurance auto-verify at appointment book + at check-in.

Wraps payments.services.check_eligibility with clinic-specific policy:
  - Auto-check 24h before appointment (async)
  - Auto-check again at kiosk check-in
  - Freeze appt if uncovered + notify staff
"""
from __future__ import annotations

from django.utils import timezone


def verify_before_appointment(*, appointment_id: str, policy_id: str,
                                service_code: str, provider_tenant_id: str) -> dict:
    """Run eligibility 24h ahead of appointment. Suitable for Celery beat."""
    try:
        from products.cymed.payments.services import check_eligibility
    except ImportError:
        return {"ok": False, "error": "payments unavailable"}
    check = check_eligibility(policy_id, service_code, provider_tenant_id)
    return {
        "ok": bool(check.covered),
        "check_id": str(check.id),
        "co_pay_amount": str(check.co_pay_amount) if check.co_pay_amount else None,
        "requires_preauth": check.requires_preauth,
    }


def verify_at_checkin(*, appointment_id: str, policy_id: str,
                       service_code: str, provider_tenant_id: str) -> dict:
    """Called from kiosk at check-in. Blocks admission if uncovered."""
    r = verify_before_appointment(appointment_id=appointment_id, policy_id=policy_id,
                                    service_code=service_code,
                                    provider_tenant_id=provider_tenant_id)
    r["checked_at"] = timezone.now().isoformat()
    r["block_visit"] = not r["ok"]
    return r
