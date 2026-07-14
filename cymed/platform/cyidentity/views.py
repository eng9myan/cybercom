"""
CyIdentity DRF views. ADR-0005 + ADR-0017.

Routers exposed under `/api/v1/identity/`:
  - /healthz/                                 — liveness + summary metrics
  - /metrics                                  — Prometheus text exposition
  - /token/validate/                          — JWT validation endpoint
  - /realms/                                  — CRUD + lifecycle actions
  - /identity-providers/                      — federation
  - /clients/                                 — OAuth/OIDC app registration
  - /clients/{id}/rotate-secret/              — secret rotation
  - /roles/                                   — RBAC roles
  - /permissions/                             — permission catalog
  - /role-assignments/                        — role→permission mapping
  - /groups/                                  — ABAC groups
  - /group-memberships/                       — user→group membership
  - /users/                                   — user profiles + provisioning
  - /sessions/                                — session list/revoke
  - /login-audits/                            — authN event log
  - /devices/                                 — device registration
  - /webauthn-credentials/                    — WebAuthn / passkeys
  - /break-glass/                             — emergency access lifecycle
  - /service-principals/                      — M2M workload identities
"""

from __future__ import annotations

import logging

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from platform.cyidentity.models import (
    ApplicationClient,
    BreakGlassAccess,
    ClientSecret,
    DeviceRegistration,
    Group,
    GroupMembership,
    IdentityProvider,
    IdentityRealm,
    LoginAudit,
    Permission,
    RealmStatus,
    Role,
    RoleAssignment,
    ServicePrincipal,
    UserProfile,
    UserSession,
    WebAuthnCredential,
)
from platform.cyidentity.permissions import (
    BreakGlassRequiresDualApproval,
    IsPlatformAdmin,
    ReadOnlyOrPlatformAdmin,
)
from platform.cyidentity.serializers import (
    ApplicationClientRegisterSerializer,
    ApplicationClientSerializer,
    BreakGlassAccessSerializer,
    BreakGlassActivateSerializer,
    BreakGlassApproveSerializer,
    BreakGlassRequestSerializer,
    ClientSecretCreateResponseSerializer,
    ClientSecretSerializer,
    DeviceRegistrationSerializer,
    GroupMembershipSerializer,
    GroupSerializer,
    IdentityHealthSerializer,
    IdentityProviderSerializer,
    IdentityRealmProvisionSerializer,
    IdentityRealmSerializer,
    LoginAuditSerializer,
    PermissionSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
    ServicePrincipalSerializer,
    TokenValidateRequestSerializer,
    TokenValidateResponseSerializer,
    UserProfileSerializer,
    UserProvisionSerializer,
    UserSessionSerializer,
    WebAuthnCredentialSerializer,
)
from platform.cyidentity.services import (
    BreakGlassService,
    ClientService,
    KeycloakError,
    RealmService,
    SessionService,
    TokenValidationError,
    TokenValidator,
    UserProvisioningService,
    render_prometheus,
)

logger = logging.getLogger("cybercom.cyidentity.views")


# ---------------------------------------------------------------------------
# Health & metrics
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def identity_health(request):
    payload = {
        "status": "ok",
        "realm_count": IdentityRealm.objects.count(),
        "active_realm_count": IdentityRealm.objects.filter(status=RealmStatus.ACTIVE).count(),
        "active_session_count": UserSession.objects.filter(status="active").count(),
        "keycloak_enabled": getattr(request, "KEYCLOAK_ENABLED", True),
    }
    return Response(IdentityHealthSerializer(payload).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def identity_metrics(request):
    return HttpResponse(render_prometheus(), content_type="text/plain; version=0.0.4")


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def token_validate(request):
    serializer = TokenValidateRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validator = TokenValidator()
    try:
        claims = validator.validate(
            serializer.validated_data["token"],
            audience=serializer.validated_data.get("audience") or None,
        )
        return Response(
            TokenValidateResponseSerializer(
                {
                    "valid": True,
                    "subject": claims.get("sub", ""),
                    "issuer": claims.get("iss", ""),
                    "audience": claims.get("aud", "")
                    if isinstance(claims.get("aud"), str)
                    else (claims.get("aud", [""])[0] if claims.get("aud") else ""),
                    "expires_at": claims.get("exp", 0),
                    "scope": claims.get("scope", ""),
                }
            ).data
        )
    except TokenValidationError:
        return Response(
            TokenValidateResponseSerializer(
                {"valid": False, "subject": "", "issuer": "", "audience": "", "scope": ""}
            ).data,
            status=status.HTTP_401_UNAUTHORIZED,
        )


# ---------------------------------------------------------------------------
# Realms
# ---------------------------------------------------------------------------
class IdentityRealmViewSet(viewsets.ModelViewSet):
    queryset = IdentityRealm.objects.all().order_by("realm_name")
    serializer_class = IdentityRealmSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]

    def get_permissions(self):
        if self.action in {"provision"}:
            return [IsPlatformAdmin()]
        return super().get_permissions()

    @action(detail=False, methods=["post"], url_path="provision")
    def provision(self, request):
        serializer = IdentityRealmProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            realm = RealmService().provision(**serializer.validated_data)
        except KeycloakError as exc:
            return Response(
                {"detail": str(exc), "keycloak_status": exc.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(IdentityRealmSerializer(realm).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        realm = self.get_object()
        return Response(IdentityRealmSerializer(RealmService().activate(realm)).data)

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        realm = self.get_object()
        reason = request.data.get("reason", "")
        return Response(IdentityRealmSerializer(RealmService().suspend(realm, reason=reason)).data)

    @action(detail=True, methods=["post"])
    def decommission(self, request, pk=None):
        realm = self.get_object()
        return Response(IdentityRealmSerializer(RealmService().decommission(realm)).data)


# ---------------------------------------------------------------------------
# Identity Provider (federation)
# ---------------------------------------------------------------------------
class IdentityProviderViewSet(viewsets.ModelViewSet):
    queryset = IdentityProvider.objects.all().order_by("alias")
    serializer_class = IdentityProviderSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


# ---------------------------------------------------------------------------
# Service principals
# ---------------------------------------------------------------------------
class ServicePrincipalViewSet(viewsets.ModelViewSet):
    queryset = ServicePrincipal.objects.all().order_by("name")
    serializer_class = ServicePrincipalSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


# ---------------------------------------------------------------------------
# Application clients + secrets
# ---------------------------------------------------------------------------
class ApplicationClientViewSet(viewsets.ModelViewSet):
    queryset = ApplicationClient.objects.all().order_by("client_id")
    serializer_class = ApplicationClientSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = ApplicationClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            realm = IdentityRealm.objects.get(pk=serializer.validated_data["realm_id"])
        except IdentityRealm.DoesNotExist:
            return Response({"detail": "Realm not found"}, status=status.HTTP_404_NOT_FOUND)
        client = ClientService().register(
            realm, **{k: v for k, v in serializer.validated_data.items() if k != "realm_id"}
        )
        return Response(ApplicationClientSerializer(client).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="rotate-secret")
    def rotate_secret(self, request, pk=None):
        client = self.get_object()
        created_by = request.data.get("created_by", "") or "api"
        row, cleartext = ClientService().rotate_secret(client, created_by=created_by)
        return Response(
            ClientSecretCreateResponseSerializer(
                {
                    "id": row.id,
                    "client_id": client.client_id,
                    "cleartext": cleartext,
                    "secret_hint": row.secret_hint,
                    "expires_at": row.expires_at,
                    "rotated_at": timezone.now(),
                }
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ClientSecretViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClientSecret.objects.all().order_by("-created_at")
    serializer_class = ClientSecretSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


# ---------------------------------------------------------------------------
# Roles / Permissions
# ---------------------------------------------------------------------------
class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all().order_by("scope", "action", "resource")
    serializer_class = PermissionSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class RoleAssignmentViewSet(viewsets.ModelViewSet):
    queryset = RoleAssignment.objects.all().order_by("-created_at")
    serializer_class = RoleAssignmentSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


# ---------------------------------------------------------------------------
# Groups / Memberships
# ---------------------------------------------------------------------------
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("path")
    serializer_class = GroupSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all().order_by("-created_at")
    serializer_class = GroupMembershipSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().order_by("username")
    serializer_class = UserProfileSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]

    @action(detail=False, methods=["post"], url_path="provision")
    def provision(self, request):
        serializer = UserProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            realm = IdentityRealm.objects.get(pk=serializer.validated_data["realm_id"])
        except IdentityRealm.DoesNotExist:
            return Response({"detail": "Realm not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = UserProvisioningService().provision_user(
                realm, **{k: v for k, v in serializer.validated_data.items() if k != "realm_id"}
            )
        except KeycloakError as exc:
            return Response(
                {"detail": str(exc), "keycloak_status": exc.status_code},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        user = self.get_object()
        user.locked_until = timezone.now() + timezone.timedelta(minutes=15)
        user.save(update_fields=["locked_until", "updated_at"])
        return Response(UserProfileSerializer(user).data)

    @action(detail=True, methods=["post"])
    def unlock(self, request, pk=None):
        user = self.get_object()
        user.locked_until = None
        user.failed_login_count = 0
        user.save(update_fields=["locked_until", "failed_login_count", "updated_at"])
        return Response(UserProfileSerializer(user).data)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
class UserSessionViewSet(viewsets.ModelViewSet):
    queryset = UserSession.objects.all().order_by("-started_at")
    serializer_class = UserSessionSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        session = self.get_object()
        reason = request.data.get("reason", "admin_action")
        return Response(UserSessionSerializer(SessionService().revoke(session, reason)).data)

    @action(detail=False, methods=["post"], url_path="enforce-idle-timeout")
    def enforce_idle_timeout(self, request):
        revoked = SessionService().enforce_idle_timeout()
        return Response({"revoked_count": revoked})


# ---------------------------------------------------------------------------
# Login audits
# ---------------------------------------------------------------------------
class LoginAuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoginAudit.objects.all().order_by("-created_at")
    serializer_class = LoginAuditSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


# ---------------------------------------------------------------------------
# Devices / WebAuthn
# ---------------------------------------------------------------------------
class DeviceRegistrationViewSet(viewsets.ModelViewSet):
    queryset = DeviceRegistration.objects.all().order_by("-created_at")
    serializer_class = DeviceRegistrationSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


class WebAuthnCredentialViewSet(viewsets.ModelViewSet):
    queryset = WebAuthnCredential.objects.all().order_by("-created_at")
    serializer_class = WebAuthnCredentialSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin]


# ---------------------------------------------------------------------------
# Break-glass
# ---------------------------------------------------------------------------
class BreakGlassAccessViewSet(viewsets.ModelViewSet):
    queryset = BreakGlassAccess.objects.all().order_by("-requested_at")
    serializer_class = BreakGlassAccessSerializer
    permission_classes = [ReadOnlyOrPlatformAdmin, BreakGlassRequiresDualApproval]

    def get_permissions(self):
        # approve + activate require explicit permission instance
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = BreakGlassRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserProfile.objects.get(pk=serializer.validated_data["user_id"])
            realm = IdentityRealm.objects.get(pk=serializer.validated_data["realm_id"])
        except (UserProfile.DoesNotExist, IdentityRealm.DoesNotExist):
            return Response({"detail": "User or realm not found"}, status=status.HTTP_404_NOT_FOUND)
        access = BreakGlassService().request(
            user=user,
            realm=realm,
            reason=serializer.validated_data["reason"],
            justification=serializer.validated_data["justification"],
            target_resource=serializer.validated_data["target_resource"],
            target_action=serializer.validated_data["target_action"],
        )
        return Response(BreakGlassAccessSerializer(access).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        access = self.get_object()
        serializer = BreakGlassApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            BreakGlassAccessSerializer(
                BreakGlassService().approve(access, **serializer.validated_data)
            ).data
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        access = self.get_object()
        serializer = BreakGlassActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            BreakGlassAccessSerializer(
                BreakGlassService().activate(access, **serializer.validated_data)
            ).data
        )

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        access = self.get_object()
        access.revoke()
        return Response(BreakGlassAccessSerializer(access).data)
