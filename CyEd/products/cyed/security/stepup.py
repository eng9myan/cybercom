"""
Step-up authorisation.

A bearer token can live for many minutes and can be stolen. Operations that
move money, expose a cohort's PII, or change who can do what should require
proof that the *human* was present recently — not merely that a token exists.

Usage:
    from products.cyed.security.stepup import RequiresRecentMfa

    class PayrollRunViewSet(...):
        @action(detail=True, methods=["post"], permission_classes=[RequiresRecentMfa])
        def mark_paid(self, request, pk=None): ...
"""

from rest_framework.permissions import BasePermission

from products.cyed.governance.access import _email
from products.cyed.security import services


class RequiresRecentMfa(BasePermission):
    """
    Allows the request only if the caller passed MFA inside the step-up window.

    Deliberately fails closed: a user with no enrolment cannot satisfy it. That
    is the intended behaviour for a control designed to protect the most
    sensitive actions — the remedy is to enrol, not to bypass.
    """

    message = (
        "This action requires recent multi-factor verification. "
        "Verify at /api/v1/security/mfa/verify/ and retry."
    )

    def has_permission(self, request, view) -> bool:
        if getattr(request, "auth_claims", None) is None:
            return False
        email = _email(request)
        if not email:
            return False
        tenant_id = getattr(request, "tenant_id", None)
        if tenant_id is None:
            return False
        allowed = services.has_recent_mfa(tenant_id, email)
        if not allowed:
            from products.cyed.security.models import SecurityEvent

            services.record_event(
                tenant_id, SecurityEvent.STEP_UP_DENIED, actor=email,
                detail=f"{request.method} {request.path}"[:255], severity="warning",
            )
        return allowed
