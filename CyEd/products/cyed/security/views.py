"""
MFA endpoints.

Every route acts on the *caller's own* enrolment, derived from the verified
token — no endpoint takes a target email. That is what makes it impossible for
one user to enrol, verify, or disable MFA on behalf of another.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core.permissions import IsAuthenticatedViaClaims
from products.cyed.governance.access import ADMIN, LEADERSHIP, IsStaff, _email, has_any, roles_of
from products.cyed.security import services
from products.cyed.security.models import LoginAttempt, MfaEnrollment, SecurityEvent
from products.cyed.security.serializers import (
    LoginAttemptSerializer, MfaEnrollmentSerializer, SecurityEventSerializer,
)


def _client_ip(request) -> str:
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if fwd:
        return fwd.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "")[:45]


def _agent(request) -> str:
    return (request.META.get("HTTP_USER_AGENT") or "")[:255]


class _MfaBase(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def _ctx(self, request):
        return {
            "tenant_id": request.tenant_id,
            "email": _email(request),
            "ip": _client_ip(request),
            "user_agent": _agent(request),
        }


class MfaStatusView(_MfaBase):
    """GET — the caller's own MFA state."""

    def get(self, request):
        c = self._ctx(request)
        return Response(services.status_for(c["tenant_id"], c["email"]))


class MfaEnrollView(_MfaBase):
    """
    POST — issue a TOTP secret for the caller.

    This is the only response that ever contains the secret, and the enrolment
    is inert until confirmed.
    """

    def post(self, request):
        c = self._ctx(request)
        if not c["email"]:
            return Response({"detail": "Your token carries no email; cannot enrol."}, status=400)
        try:
            enrollment, secret, uri = services.start_enrollment(
                c["tenant_id"], c["email"], label=request.data.get("label", "")[:100]
            )
        except services.MfaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        services.record_event(c["tenant_id"], SecurityEvent.MFA_ENROLLED, actor=c["email"],
                              roles=",".join(sorted(roles_of(request))), ip=c["ip"],
                              user_agent=c["user_agent"], detail="Secret issued (unconfirmed)")
        return Response({
            "enrollment": str(enrollment.id),
            "secret": secret,
            "otpauth_uri": uri,
            "confirmed": False,
            "next": "Scan the URI in an authenticator app, then POST the 6-digit code to /mfa/confirm/.",
        }, status=status.HTTP_201_CREATED)


class MfaConfirmView(_MfaBase):
    """POST {code} — activate MFA and receive backup codes (shown once)."""

    def post(self, request):
        c = self._ctx(request)
        try:
            _, codes = services.confirm_enrollment(
                c["tenant_id"], c["email"], request.data.get("code", ""),
                ip=c["ip"], user_agent=c["user_agent"],
            )
        except services.MfaLockedOut as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except services.MfaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "confirmed": True,
            "backup_codes": codes,
            "warning": "These codes are shown once. Store them somewhere safe.",
        })


class MfaVerifyView(_MfaBase):
    """POST {code} — verify a TOTP or backup code and open a step-up window."""

    def post(self, request):
        c = self._ctx(request)
        try:
            _, method, session = services.verify_code(
                c["tenant_id"], c["email"], request.data.get("code", ""),
                ip=c["ip"], user_agent=c["user_agent"],
            )
        except services.MfaLockedOut as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except services.MfaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "verified": True,
            "method": method,
            "step_up_expires_at": session.expires_at if session else None,
        })


class MfaDisableView(_MfaBase):
    """POST {code} — turn MFA off; requires passing MFA first."""

    def post(self, request):
        c = self._ctx(request)
        try:
            services.disable(c["tenant_id"], c["email"], request.data.get("code", ""),
                             ip=c["ip"], user_agent=c["user_agent"])
        except services.MfaLockedOut as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except services.MfaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"disabled": True})


class MfaBackupCodesView(_MfaBase):
    """POST {code} — regenerate backup codes; invalidates the previous set."""

    def post(self, request):
        c = self._ctx(request)
        try:
            enrollment, _, _ = services.verify_code(
                c["tenant_id"], c["email"], request.data.get("code", ""),
                ip=c["ip"], user_agent=c["user_agent"], create_session=False,
            )
        except services.MfaLockedOut as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except services.MfaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        codes = services.generate_backup_codes(enrollment)
        services.record_event(c["tenant_id"], SecurityEvent.MFA_BACKUP_REGENERATED,
                              actor=c["email"], ip=c["ip"], user_agent=c["user_agent"],
                              detail="Previous codes invalidated", severity="warning")
        return Response({"backup_codes": codes,
                         "warning": "Your previous codes no longer work."})


class MfaEnrollmentViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    Administrative visibility: WHO has MFA, never their secret.

    Leadership needs to see coverage to enforce a policy; the serializer omits
    the secret entirely so this cannot become a disclosure path.
    """

    serializer_class = MfaEnrollmentSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = MfaEnrollment.objects.filter(tenant_id=self.request.tenant_id)
        if not has_any(self.request, ADMIN | LEADERSHIP):
            qs = qs.filter(user_email=_email(self.request).lower())
        return qs

    @action(detail=False, methods=["get"])
    def coverage(self, request):
        """What proportion of staff actually have a second factor."""
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Leadership only."}, status=status.HTTP_403_FORBIDDEN)
        from products.cyed.hr.models import Staff

        total = Staff.objects.filter(tenant_id=request.tenant_id, is_active=True).count()
        emails = set(
            e.lower() for e in Staff.objects.filter(
                tenant_id=request.tenant_id, is_active=True
            ).values_list("email", flat=True) if e
        )
        enrolled = MfaEnrollment.objects.filter(
            tenant_id=request.tenant_id, confirmed=True, user_email__in=emails
        ).count()
        return Response({
            "active_staff": total,
            "with_mfa": enrolled,
            "without_mfa": max(total - enrolled, 0),
            "coverage_pct": round((enrolled / total * 100), 1) if total else 0.0,
        })


class SecurityEventViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Append-only security audit trail. Leadership only — it names people."""

    serializer_class = SecurityEventSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        if not has_any(self.request, ADMIN | LEADERSHIP):
            return SecurityEvent.objects.none()
        qs = SecurityEvent.objects.filter(tenant_id=self.request.tenant_id)
        params = self.request.query_params
        if params.get("event_type"):
            qs = qs.filter(event_type=params["event_type"])
        if params.get("severity"):
            qs = qs.filter(severity=params["severity"])
        return qs


class LoginAttemptViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = LoginAttemptSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        if not has_any(self.request, ADMIN | LEADERSHIP):
            return LoginAttempt.objects.none()
        return LoginAttempt.objects.filter(tenant_id=self.request.tenant_id)
