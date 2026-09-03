"""Closed-loop referral state machine."""
from __future__ import annotations

from django.utils import timezone

from .models import Referral


def create_and_send(*, from_tenant_id, to_tenant_id, target_kind: str,
                     patient_profile_id, reason: str,
                     clinical_summary: str = "", urgency: str = "routine",
                     from_practitioner_id=None,
                     encounter_id=None) -> Referral:
    ref = Referral.objects.create(
        from_tenant_id=from_tenant_id, to_tenant_id=to_tenant_id,
        target_kind=target_kind, patient_profile_id=patient_profile_id,
        reason=reason[:400], clinical_summary=clinical_summary,
        urgency=urgency, from_practitioner_id=from_practitioner_id,
        encounter_id=encounter_id,
        status="sent", sent_at=timezone.now(),
    )
    return ref


def acknowledge(*, referral_id, to_practitioner_id=None) -> Referral:
    r = Referral.objects.get(id=referral_id)
    r.status = "acknowledged"
    r.acknowledged_at = timezone.now()
    if to_practitioner_id:
        r.to_practitioner_id = to_practitioner_id
    r.save(update_fields=["status", "acknowledged_at", "to_practitioner_id", "updated_at"])
    return r


def schedule(*, referral_id) -> Referral:
    r = Referral.objects.get(id=referral_id)
    r.status = "scheduled"
    r.scheduled_at = timezone.now()
    r.save(update_fields=["status", "scheduled_at", "updated_at"])
    return r


def complete(*, referral_id, notes: str = "") -> Referral:
    r = Referral.objects.get(id=referral_id)
    r.status = "completed"
    r.completed_at = timezone.now()
    if notes:
        r.notes = notes
    r.save(update_fields=["status", "completed_at", "notes", "updated_at"])
    return r


def share_result(*, referral_id, documents: list[dict]) -> Referral:
    r = Referral.objects.get(id=referral_id)
    r.status = "result_shared"
    r.result_shared_at = timezone.now()
    r.result_documents = documents
    r.save(update_fields=["status", "result_shared_at",
                            "result_documents", "updated_at"])
    return r
