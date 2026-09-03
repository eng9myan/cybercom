"""Kiosk state machine."""
from __future__ import annotations

from django.utils import timezone

from .models import KioskSession


def start(*, kiosk_id: str, appointment_id: str | None = None) -> KioskSession:
    return KioskSession.objects.create(kiosk_id=kiosk_id, appointment_id=appointment_id)


def identify(*, session_id: str, patient_profile_id: str, method: str) -> KioskSession:
    s = KioskSession.objects.get(id=session_id)
    s.patient_profile_id = patient_profile_id
    s.identity_method = method
    s.stage = "identified"
    s.save(update_fields=["patient_profile_id", "identity_method", "stage", "updated_at"])
    return s


def verify_insurance(*, session_id: str, policy_id: str, service_code: str,
                       provider_tenant_id: str) -> KioskSession:
    from products.cymed.clinic.insurance_verify.services import verify_at_checkin

    s = KioskSession.objects.get(id=session_id)
    result = verify_at_checkin(appointment_id=str(s.appointment_id) if s.appointment_id else "",
                                 policy_id=policy_id, service_code=service_code,
                                 provider_tenant_id=provider_tenant_id)
    if result["ok"]:
        s.stage = "insurance_verified"
        s.save(update_fields=["stage", "updated_at"])
    else:
        s.stage = "failed_verify"
        s.error_note = "Insurance not covered / not eligible"
        s.save(update_fields=["stage", "error_note", "updated_at"])
    return s


def sign_consent(*, session_id: str) -> KioskSession:
    s = KioskSession.objects.get(id=session_id)
    s.stage = "consent_signed"
    s.save(update_fields=["stage", "updated_at"])
    return s


def complete(*, session_id: str) -> KioskSession:
    s = KioskSession.objects.get(id=session_id)
    now = timezone.now()
    s.stage = "completed"
    s.completed_at = now
    s.duration_seconds = int((now - s.started_at).total_seconds())
    s.save(update_fields=["stage", "completed_at", "duration_seconds", "updated_at"])
    return s
