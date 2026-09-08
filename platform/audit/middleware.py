"""
M-11 — PHI-access audit trail.

The hash-chained audit sink (AuditService, ADR-0028) was fully built but
nothing called it for API traffic, so `platform_audit_events` stayed empty —
a hard HIPAA / GDPR / NPHIES / Hakeem compliance failure. This middleware
records a hash-chained AuditEvent for every request that reads or writes
clinical / PHI data through the API.

Coarse by design (path + method + actor + outcome). Fine-grained
before/after-state auditing is a per-viewset concern layered on top later;
this closes the "no audit trail at all" gap.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("platform.audit.phi")

# API path segments (right after /api/v1/) whose data is clinical / PHI.
_PHI_SEGMENTS = {
    "patients", "encounters", "clinical", "orders", "careplans", "consents",
    "pharmacy", "lab", "imaging", "hospital", "rcm", "ai-cds", "scheduling",
    "providers", "provider-portal", "patient-portal", "patient-app",
    "registries", "documents", "mrff", "ecosystem", "integration", "integrations",
}
_VERB_BY_METHOD = {
    "GET": "read", "HEAD": "read", "OPTIONS": "read",
    "POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete",
}


class PHIAccessAuditMiddleware:
    """Emits a hash-chained AuditEvent for clinical/PHI API access.

    Must sit AFTER CyIdentityAuthMiddleware and the tenant middleware so
    `request.user_session` / `request.tenant_id` are populated.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._maybe_record(request, response)
        except Exception:  # auditing must never break the response
            logger.exception("PHI audit record failed for %s %s", request.method, request.path)
        return response

    @staticmethod
    def _segments(path: str):
        parts = [p for p in path.split("/") if p]
        # tolerate both /api/v1/<seg>/... and /api/<seg>/...
        if parts[:2] == ["api", "v1"]:
            return parts[2:]
        if parts[:1] == ["api"]:
            return parts[1:]
        return []

    def _maybe_record(self, request, response):
        segs = self._segments(request.path)
        if not segs or segs[0] not in _PHI_SEGMENTS:
            return

        # Import here so the module is import-safe before apps are ready.
        from platform.audit.models import AuditCategoryCode, AuditStatus, DataClassification
        from platform.audit.services import AuditService

        session = getattr(request, "user_session", None) or {}
        claims = getattr(request, "auth_claims", None) or {}
        tenant_id = getattr(request, "tenant_id", None) or session.get("tenant_id")

        verb = _VERB_BY_METHOD.get(request.method, "read")
        resource_type = segs[0]
        # /api/v1/patients/<uuid>/... -> resource_id is the 2nd segment when it
        # is not itself a sub-collection name.
        resource_id = ""
        if len(segs) > 1 and "-" in segs[1] or (len(segs) > 1 and len(segs[1]) >= 16):
            resource_id = segs[1]

        sc = getattr(response, "status_code", 0)
        if sc == 403 or sc == 401:
            status = AuditStatus.DENIED
            action_verb = "permission_denied"
        elif sc >= 400:
            status = AuditStatus.FAILURE
            action_verb = verb
        else:
            status = AuditStatus.SUCCESS
            action_verb = verb

        AuditService().record(
            action=f"{resource_type}.{verb}",
            action_verb=action_verb if action_verb in {
                "create", "read", "update", "delete", "permission_denied",
            } else "read",
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            actor_user_id=str(session.get("user_id") or claims.get("sub") or ""),
            actor_username=str(session.get("email") or claims.get("email") or ""),
            actor_role_claims=list(session.get("roles") or []),
            actor_ip=request.META.get("REMOTE_ADDR"),
            actor_session_id=str(session.get("session_id") or ""),
            category=AuditCategoryCode.CLINICAL,
            data_classification=DataClassification.PHI,
            # ADR-0028 S5.2: purpose_of_use is mandatory for clinical events.
            purpose_of_use=(
                request.headers.get("X-Purpose-Of-Use")
                or request.headers.get("X-Purpose-of-Use")
                or "treatment"
            ),
            correlation_id=request.headers.get("X-Request-ID", "")[:64],
            status=status,
            outcome_description=f"HTTP {sc} {request.method} {request.path}",
        )
