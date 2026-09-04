"""Closed-loop referral state machine.

Cross-tenant by design: `from_tenant_id` shares the referral (and its
`clinical_summary`) with `to_tenant_id`. Sending a referral records a
time-boxed `ConsentGrant` (canonical-data-model-v1.md §5.1); the receiving
tenant's actions on the referral are gated on that grant.
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from platform.canonical import events
from platform.canonical.consent import require_consent
from platform.canonical.models import ConsentGrant

from .models import Referral

_CONSENT_TTL = timedelta(days=90)
_SCOPE = {"entities": ["Referral"], "purpose": "care_coordination"}


def _guard(ref: Referral) -> None:
    """The receiving tenant may only act on a referral it has consent for."""
    require_consent(
        ref.from_tenant_id,
        grantee_tenant_id=ref.to_tenant_id,
        entity="Referral",
        purpose="care_coordination",
    )


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

    ConsentGrant.objects.update_or_create(
        tenant_id=from_tenant_id,
        grantee_tenant_id=to_tenant_id,
        scope=_SCOPE,
        defaults={
            "granted_by": from_practitioner_id,
            "expires_at": timezone.now() + _CONSENT_TTL,
            "status": "active",
            "revoked_at": None,
        },
    )

    events.emit(
        event_type="cymed.referral.sent",
        aggregate_type="Referral",
        aggregate_id=ref.id,
        tenant_id=from_tenant_id,
        payload={
            "referral_id": str(ref.id),
            "to_tenant_id": str(to_tenant_id),
            "target_kind": target_kind,
            "urgency": urgency,
        },
    )
    return ref


def acknowledge(*, referral_id, to_practitioner_id=None) -> Referral:
    r = Referral.objects.get(id=referral_id)
    _guard(r)
    r.status = "acknowledged"
    r.acknowledged_at = timezone.now()
    if to_practitioner_id:
        r.to_practitioner_id = to_practitioner_id
    r.save(update_fields=["status", "acknowledged_at", "to_practitioner_id", "updated_at"])
    return r


def schedule(*, referral_id) -> Referral:
    r = Referral.objects.get(id=referral_id)
    _guard(r)
    r.status = "scheduled"
    r.scheduled_at = timezone.now()
    r.save(update_fields=["status", "scheduled_at", "updated_at"])
    return r


def complete(*, referral_id, notes: str = "") -> Referral:
    r = Referral.objects.get(id=referral_id)
    _guard(r)
    r.status = "completed"
    r.completed_at = timezone.now()
    if notes:
        r.notes = notes
    r.save(update_fields=["status", "completed_at", "notes", "updated_at"])
    return r


def share_result(*, referral_id, documents: list[dict]) -> Referral:
    r = Referral.objects.get(id=referral_id)
    _guard(r)
    r.status = "result_shared"
    r.result_shared_at = timezone.now()
    r.result_documents = documents
    r.save(update_fields=["status", "result_shared_at",
                            "result_documents", "updated_at"])
    events.emit(
        event_type="cymed.referral.result_shared",
        aggregate_type="Referral",
        aggregate_id=r.id,
        tenant_id=r.from_tenant_id,
        payload={"referral_id": str(r.id), "documents": len(documents)},
    )
    return r
