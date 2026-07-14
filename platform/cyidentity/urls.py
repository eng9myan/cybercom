"""
CyIdentity URL configuration. Mounted at `/api/v1/identity/`.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platform.cyidentity import views as v

router = DefaultRouter()
router.register(r"realms", v.IdentityRealmViewSet, basename="realm")
router.register(r"identity-providers", v.IdentityProviderViewSet, basename="identity-provider")
router.register(r"service-principals", v.ServicePrincipalViewSet, basename="service-principal")
router.register(r"clients", v.ApplicationClientViewSet, basename="client")
router.register(r"client-secrets", v.ClientSecretViewSet, basename="client-secret")
router.register(r"permissions", v.PermissionViewSet, basename="permission")
router.register(r"roles", v.RoleViewSet, basename="role")
router.register(r"role-assignments", v.RoleAssignmentViewSet, basename="role-assignment")
router.register(r"groups", v.GroupViewSet, basename="group")
router.register(r"group-memberships", v.GroupMembershipViewSet, basename="group-membership")
router.register(r"users", v.UserProfileViewSet, basename="user")
router.register(r"sessions", v.UserSessionViewSet, basename="session")
router.register(r"login-audits", v.LoginAuditViewSet, basename="login-audit")
router.register(r"devices", v.DeviceRegistrationViewSet, basename="device")
router.register(
    r"webauthn-credentials", v.WebAuthnCredentialViewSet, basename="webauthn-credential"
)
router.register(r"break-glass", v.BreakGlassAccessViewSet, basename="break-glass")

urlpatterns = [
    path("healthz/", v.identity_health, name="cyidentity-health"),
    path("metrics", v.identity_metrics, name="cyidentity-metrics"),
    path("token/validate/", v.token_validate, name="cyidentity-token-validate"),
    path("", include(router.urls)),
]
