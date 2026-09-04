"""Cross-provider referral routing — routing a referral grants the target
tenant consent; acknowledge/decline are consent-gated; a canonical
DomainEvent is emitted on routing."""

import uuid

import pytest

from platform.canonical.consent import ConsentDenied
from platform.canonical.models import ConsentGrant, DomainEvent
from platform.common.tenant_context import tenant_context
from products.cymed.ecosystem.referral_routing import services
from products.cymed.ecosystem.referral_routing.models import NetworkReferral, RoutingRule

SRC = uuid.uuid4()
TGT = uuid.uuid4()


def _rule():
    return RoutingRule.objects.create(
        tenant_id=SRC, code="R1", name="lab default",
        source_kind="clinic", target_kind="lab", specialty="",
        preferred_tenant_ids=[str(TGT)], fallback_tenant_ids=[], payer_ids=[],
        active=True, priority=100,
    )


@pytest.mark.django_db
def test_route_grants_consent_and_emits_event():
    with tenant_context(SRC):
        _rule()
        ref = services.route_referral(
            source_tenant_id=SRC, source_provider_id=uuid.uuid4(),
            target_kind="lab", patient_profile_id=uuid.uuid4(),
            reason="CBC", clinical_summary="routine screen",
        )
    assert ref.status == NetworkReferral.Status.ROUTED
    assert str(ref.target_tenant_id) == str(TGT)

    assert ConsentGrant.objects.filter(
        tenant_id=SRC, grantee_tenant_id=TGT, status="active"
    ).exists()
    assert DomainEvent.objects.filter(
        tenant_id=SRC, event_type="cymed.network_referral.routed", aggregate_id=ref.id
    ).exists()


@pytest.mark.django_db
def test_target_can_acknowledge_with_consent():
    with tenant_context(SRC):
        _rule()
        ref = services.route_referral(
            source_tenant_id=SRC, source_provider_id=None, target_kind="lab",
            patient_profile_id=uuid.uuid4(), reason="CBC",
        )
    with tenant_context(TGT):
        r = services.acknowledge(referral_id=ref.id, target_provider_id=uuid.uuid4())
    assert r.status == NetworkReferral.Status.ACKNOWLEDGED


@pytest.mark.django_db
def test_target_blocked_after_consent_revoked():
    with tenant_context(SRC):
        _rule()
        ref = services.route_referral(
            source_tenant_id=SRC, source_provider_id=None, target_kind="lab",
            patient_profile_id=uuid.uuid4(), reason="CBC",
        )
        ConsentGrant.objects.filter(tenant_id=SRC, grantee_tenant_id=TGT).update(
            status="revoked"
        )
    with tenant_context(TGT), pytest.raises(ConsentDenied):
        services.acknowledge(referral_id=ref.id, target_provider_id=None)
