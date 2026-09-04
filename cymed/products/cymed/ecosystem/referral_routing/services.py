"""Domain services powering cross-provider referral routing decisions."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Iterable, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from platform.canonical import events
from platform.canonical.consent import require_consent
from platform.canonical.models import ConsentGrant

from .models import NetworkReferral, RoutingLog, RoutingRule

_CONSENT_TTL = timedelta(days=90)
_CONSENT_SCOPE = {"entities": ["Referral"], "purpose": "care_coordination"}


def _grant_consent(*, grantor, grantee, granted_by=None) -> None:
    """A source tenant routing a referral to a target tenant is consenting to
    share it (canonical-data-model-v1.md §5.1)."""
    ConsentGrant.objects.update_or_create(
        tenant_id=grantor,
        grantee_tenant_id=grantee,
        scope=_CONSENT_SCOPE,
        defaults={
            "granted_by": granted_by,
            "expires_at": timezone.now() + _CONSENT_TTL,
            "status": "active",
            "revoked_at": None,
        },
    )


def _guard(referral: NetworkReferral) -> None:
    """The target tenant may only act on a referral it has consent for."""
    if referral.target_tenant_id:
        require_consent(
            referral.source_tenant_id,
            grantee_tenant_id=referral.target_tenant_id,
            entity="Referral",
            purpose="care_coordination",
        )


def _coerce_list(value: Optional[Iterable[Any]]) -> list:
    if value is None:
        return []
    return list(value)


def _find_best_rule(
    *,
    tenant_id: Optional[UUID | str],
    target_kind: str,
    specialty: str,
    urgency: str,
) -> Optional[RoutingRule]:
    base = RoutingRule.objects.filter(active=True, target_kind=target_kind)
    specialty_q = Q(specialty="") | Q(specialty__iexact=specialty)
    if specialty:
        base = base.filter(specialty_q)
    else:
        base = base.filter(specialty="")
    tenant_scoped = base.filter(tenant_id=tenant_id).order_by("-priority", "created_at")
    match = tenant_scoped.first()
    if match is not None:
        return match
    ecosystem_scoped = base.filter(tenant_id__isnull=True).order_by("-priority", "created_at")
    return ecosystem_scoped.first()


def _first_available_tenant(candidates: Iterable[Any]) -> Optional[Any]:
    for candidate in candidates:
        if candidate:
            return candidate
    return None


def create_rule(
    *,
    tenant_id: Optional[UUID | str],
    code: str,
    name: str,
    source_kind: str,
    target_kind: str,
    specialty: str = "",
    urgency: str = "routine",
    geo_scope: str = "same_country",
    preferred_tenant_ids: Optional[Iterable[Any]] = None,
    fallback_tenant_ids: Optional[Iterable[Any]] = None,
    payer_ids: Optional[Iterable[Any]] = None,
    priority: int = 100,
) -> RoutingRule:
    with transaction.atomic():
        rule = RoutingRule.objects.create(
            tenant_id=tenant_id,
            code=code,
            name=name,
            source_kind=source_kind,
            target_kind=target_kind,
            specialty=specialty,
            urgency=urgency,
            geo_scope=geo_scope,
            preferred_tenant_ids=_coerce_list(preferred_tenant_ids),
            fallback_tenant_ids=_coerce_list(fallback_tenant_ids),
            payer_ids=_coerce_list(payer_ids),
            priority=priority,
        )
    return rule


def route_referral(
    *,
    source_tenant_id: UUID | str,
    source_provider_id: Optional[UUID | str],
    target_kind: str,
    patient_profile_id: UUID | str,
    reason: str,
    clinical_summary: str = "",
    urgency: str = "routine",
    specialty: str = "",
    preferred_locations: Optional[Iterable[Any]] = None,
    consent_grant_id: Optional[UUID | str] = None,
) -> NetworkReferral:
    with transaction.atomic():
        referral = NetworkReferral.objects.create(
            source_tenant_id=source_tenant_id,
            source_provider_id=source_provider_id,
            target_kind=target_kind,
            patient_profile_id=patient_profile_id,
            reason=reason,
            clinical_summary=clinical_summary,
            urgency=urgency,
            preferred_locations=_coerce_list(preferred_locations),
            consent_grant_id=consent_grant_id,
            status=NetworkReferral.Status.CREATED,
        )
        rule = _find_best_rule(
            tenant_id=source_tenant_id,
            target_kind=target_kind,
            specialty=specialty,
            urgency=urgency,
        )
        chosen_tenant = None
        used_fallback = False
        if rule is not None:
            referral.matched_rule_id = rule.id
            RoutingLog.objects.create(
                referral=referral,
                kind=RoutingLog.Kind.RULE_MATCHED,
                rule_id=rule.id,
                reason=f"Matched rule {rule.code}",
            )
            chosen_tenant = _first_available_tenant(rule.preferred_tenant_ids)
            if chosen_tenant is None:
                chosen_tenant = _first_available_tenant(rule.fallback_tenant_ids)
                if chosen_tenant is not None:
                    used_fallback = True
        if chosen_tenant is not None:
            referral.target_tenant_id = chosen_tenant
            referral.status = NetworkReferral.Status.ROUTED
            referral.routed_at = timezone.now()
            RoutingLog.objects.create(
                referral=referral,
                kind=(
                    RoutingLog.Kind.FALLBACK_USED
                    if used_fallback
                    else RoutingLog.Kind.CANDIDATE_SELECTED
                ),
                candidate_tenant_id=chosen_tenant,
                rule_id=rule.id if rule is not None else None,
                reason="Fallback candidate selected" if used_fallback else "Preferred candidate selected",
            )
            _grant_consent(
                grantor=source_tenant_id, grantee=chosen_tenant,
                granted_by=source_provider_id,
            )
        referral.save()

        if referral.target_tenant_id:
            events.emit(
                event_type="cymed.network_referral.routed",
                aggregate_type="NetworkReferral",
                aggregate_id=referral.id,
                tenant_id=source_tenant_id,
                payload={
                    "referral_id": str(referral.id),
                    "target_tenant_id": str(referral.target_tenant_id),
                    "target_kind": target_kind,
                    "used_fallback": used_fallback,
                },
            )
    return referral


def acknowledge(
    *,
    referral_id: UUID | str,
    target_provider_id: Optional[UUID | str],
) -> NetworkReferral:
    with transaction.atomic():
        referral = NetworkReferral.objects.select_for_update().get(pk=referral_id)
        _guard(referral)
        referral.target_provider_id = target_provider_id
        referral.status = NetworkReferral.Status.ACKNOWLEDGED
        referral.acknowledged_at = timezone.now()
        referral.save()
    return referral


def decline(
    *,
    referral_id: UUID | str,
    reason: str,
) -> NetworkReferral:
    with transaction.atomic():
        referral = NetworkReferral.objects.select_for_update().get(pk=referral_id)
        _guard(referral)
        prior_tenant = referral.target_tenant_id
        RoutingLog.objects.create(
            referral=referral,
            kind=RoutingLog.Kind.CANDIDATE_DECLINED,
            candidate_tenant_id=prior_tenant,
            rule_id=referral.matched_rule_id,
            reason=reason,
        )
        next_tenant = None
        used_fallback = False
        rule: Optional[RoutingRule] = None
        if referral.matched_rule_id:
            rule = RoutingRule.objects.filter(pk=referral.matched_rule_id).first()
        if rule is not None:
            preferred = [t for t in rule.preferred_tenant_ids if t and t != prior_tenant]
            fallback = [t for t in rule.fallback_tenant_ids if t and t != prior_tenant]
            next_tenant = _first_available_tenant(preferred)
            if next_tenant is None:
                next_tenant = _first_available_tenant(fallback)
                if next_tenant is not None:
                    used_fallback = True
        if next_tenant is not None:
            referral.target_tenant_id = next_tenant
            referral.target_provider_id = None
            referral.status = NetworkReferral.Status.ROUTED
            referral.routed_at = timezone.now()
            referral.acknowledged_at = None
            RoutingLog.objects.create(
                referral=referral,
                kind=(
                    RoutingLog.Kind.FALLBACK_USED
                    if used_fallback
                    else RoutingLog.Kind.CANDIDATE_SELECTED
                ),
                candidate_tenant_id=next_tenant,
                rule_id=rule.id if rule is not None else None,
                reason="Re-routed after decline",
            )
            _grant_consent(grantor=referral.source_tenant_id, grantee=next_tenant)
        else:
            referral.status = NetworkReferral.Status.DECLINED
        referral.save()
    return referral


def manual_override(
    *,
    referral_id: UUID | str,
    target_tenant_id: UUID | str,
    target_provider_id: Optional[UUID | str] = None,
    reason: str,
) -> NetworkReferral:
    with transaction.atomic():
        referral = NetworkReferral.objects.select_for_update().get(pk=referral_id)
        referral.target_tenant_id = target_tenant_id
        referral.target_provider_id = target_provider_id
        referral.status = NetworkReferral.Status.ROUTED
        referral.routed_at = timezone.now()
        _grant_consent(grantor=referral.source_tenant_id, grantee=target_tenant_id)
        RoutingLog.objects.create(
            referral=referral,
            kind=RoutingLog.Kind.MANUAL_OVERRIDE,
            candidate_tenant_id=target_tenant_id,
            rule_id=referral.matched_rule_id,
            reason=reason,
        )
        referral.save()
    return referral


def mark_scheduled(
    *,
    referral_id: UUID | str,
    scheduled_at,
) -> NetworkReferral:
    with transaction.atomic():
        referral = NetworkReferral.objects.select_for_update().get(pk=referral_id)
        referral.scheduled_at = scheduled_at or timezone.now()
        referral.status = NetworkReferral.Status.SCHEDULED
        referral.save()
    return referral


def mark_completed(referral_id: UUID | str) -> NetworkReferral:
    with transaction.atomic():
        referral = NetworkReferral.objects.select_for_update().get(pk=referral_id)
        referral.completed_at = timezone.now()
        referral.status = NetworkReferral.Status.COMPLETED
        referral.save()
    return referral


def attach_result(
    *,
    referral_id: UUID | str,
    document_url: str,
    kind: str,
) -> NetworkReferral:
    with transaction.atomic():
        referral = NetworkReferral.objects.select_for_update().get(pk=referral_id)
        documents = list(referral.result_documents or [])
        documents.append(
            {
                "url": document_url,
                "kind": kind,
                "at": timezone.now().isoformat(),
            }
        )
        referral.result_documents = documents
        referral.status = NetworkReferral.Status.RESULT_RETURNED
        referral.save()
    return referral
