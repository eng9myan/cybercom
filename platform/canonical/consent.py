"""
Cross-tenant / cross-domain consent checks (canonical-data-model-v1.md §5.1).

A `ConsentGrant` row (owned by the grantor tenant) is the lawful basis for
another tenant — or a specific user — to read the grantor's data. Nothing
reads across the tenant boundary without a matching effective grant.

    from platform.canonical.consent import has_consent, require_consent

    if not has_consent(grantor, grantee_tenant_id=other, entity="Referral",
                       purpose="care_coordination"):
        raise PermissionDenied(...)

    # or, as a guard that raises ConsentDenied:
    require_consent(grantor, grantee_tenant_id=other, entity="Referral",
                    purpose="care_coordination")
"""
from __future__ import annotations

from django.utils import timezone

from platform.canonical.models import ConsentGrant, ConsentGrantStatus


class ConsentDenied(PermissionError):
    """No effective ConsentGrant covers the requested cross-tenant access."""


def _scope_covers(scope: dict, *, entity: str | None, purpose: str | None) -> bool:
    """An empty / missing key means "any". `scope` shape:
    {"entities": [...], "fields": [...], "purpose": "..." | [...]}"""
    if entity is not None:
        entities = scope.get("entities")
        if entities and entity not in entities:
            return False
    if purpose is not None:
        allowed = scope.get("purpose")
        if allowed:
            allowed_set = {allowed} if isinstance(allowed, str) else set(allowed)
            if purpose not in allowed_set:
                return False
    return True


def has_consent(
    grantor_tenant_id,
    *,
    grantee_tenant_id=None,
    grantee_user_id=None,
    entity: str | None = None,
    purpose: str | None = None,
    at=None,
) -> bool:
    """True iff the grantor tenant has an effective grant to this grantee that
    covers `entity` + `purpose`."""
    at = at or timezone.now()
    q = ConsentGrant.all_tenants if hasattr(ConsentGrant, "all_tenants") else ConsentGrant.objects
    grants = q.filter(tenant_id=grantor_tenant_id, status=ConsentGrantStatus.ACTIVE)
    if grantee_tenant_id is not None:
        grants = grants.filter(grantee_tenant_id=grantee_tenant_id)
    if grantee_user_id is not None:
        grants = grants.filter(grantee_user_id=grantee_user_id)
    for g in grants:
        if g.expires_at is not None and g.expires_at <= at:
            continue
        if _scope_covers(g.scope or {}, entity=entity, purpose=purpose):
            return True
    return False


def require_consent(grantor_tenant_id, **kwargs) -> None:
    """`has_consent` as a guard — raises `ConsentDenied` when it would return
    False."""
    if not has_consent(grantor_tenant_id, **kwargs):
        target = kwargs.get("grantee_tenant_id") or kwargs.get("grantee_user_id")
        raise ConsentDenied(
            f"no effective ConsentGrant from {grantor_tenant_id} to {target} "
            f"for entity={kwargs.get('entity')} purpose={kwargs.get('purpose')}"
        )
