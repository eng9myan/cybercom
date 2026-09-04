"""Closed-loop referral — sending grants time-boxed consent; the receiving
tenant's actions are consent-gated; a canonical DomainEvent is emitted."""

import uuid

import pytest

from platform.canonical.consent import ConsentDenied
from platform.canonical.models import ConsentGrant, DomainEvent
from platform.common.tenant_context import tenant_context
from products.cymed.clinic.referral_loop import services
from products.cymed.clinic.referral_loop.models import Referral

FROM_T = uuid.uuid4()
TO_T = uuid.uuid4()


@pytest.mark.django_db
def test_send_grants_consent_and_emits_event():
    with tenant_context(FROM_T):
        ref = services.create_and_send(
            from_tenant_id=FROM_T, to_tenant_id=TO_T, target_kind="hospital",
            patient_profile_id=uuid.uuid4(), reason="Chest pain workup",
            clinical_summary="55M, exertional chest pain, troponin pending.",
        )
    assert ref.status == "sent"

    grant = ConsentGrant.objects.get(tenant_id=FROM_T, grantee_tenant_id=TO_T)
    assert grant.is_effective()
    assert grant.scope["entities"] == ["Referral"]

    assert DomainEvent.objects.filter(
        tenant_id=FROM_T, event_type="cymed.referral.sent", aggregate_id=ref.id
    ).exists()


@pytest.mark.django_db
def test_receiver_can_act_with_consent():
    with tenant_context(FROM_T):
        ref = services.create_and_send(
            from_tenant_id=FROM_T, to_tenant_id=TO_T, target_kind="lab",
            patient_profile_id=uuid.uuid4(), reason="CBC",
        )
    with tenant_context(TO_T):
        services.acknowledge(referral_id=ref.id, to_practitioner_id=uuid.uuid4())
        services.schedule(referral_id=ref.id)
        r = services.complete(referral_id=ref.id, notes="Seen, results normal")
    assert r.status == "completed"


@pytest.mark.django_db
def test_receiver_blocked_when_consent_revoked():
    with tenant_context(FROM_T):
        ref = services.create_and_send(
            from_tenant_id=FROM_T, to_tenant_id=TO_T, target_kind="imaging",
            patient_profile_id=uuid.uuid4(), reason="CXR",
        )
        ConsentGrant.objects.filter(tenant_id=FROM_T, grantee_tenant_id=TO_T).update(
            status="revoked"
        )
    with tenant_context(TO_T), pytest.raises(ConsentDenied):
        services.acknowledge(referral_id=ref.id)


@pytest.mark.django_db
def test_action_on_a_referral_with_no_grant_at_all_is_denied():
    # a referral row that predates the consent wiring (created directly)
    with tenant_context(FROM_T):
        ref = Referral.objects.create(
            from_tenant_id=FROM_T, to_tenant_id=TO_T, target_kind="clinic",
            patient_profile_id=uuid.uuid4(), reason="follow-up", status="sent",
        )
    with tenant_context(TO_T), pytest.raises(ConsentDenied):
        services.schedule(referral_id=ref.id)
