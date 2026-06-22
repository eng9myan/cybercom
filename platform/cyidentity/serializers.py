"""
CyIdentity DRF serializers. ADR-0005 + ADR-0017.
"""
from __future__ import annotations

from rest_framework import serializers

from platform.cyidentity.models import (
    ApplicationClient,
    BreakGlassAccess,
    BreakGlassReason,
    ClientSecret,
    DeviceRegistration,
    Group,
    GroupMembership,
    IdentityProvider,
    IdentityRealm,
    LoginAudit,
    Permission,
    RealmConfiguration,
    RealmStatus,
    RealmType,
    Role,
    RoleAssignment,
    ServicePrincipal,
    UserProfile,
    UserSession,
    WebAuthnCredential,
)


# ---------------------------------------------------------------------------
# Realm
# ---------------------------------------------------------------------------
class RealmConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealmConfiguration
        fields = [
            "id",
            "access_token_lifetime_seconds",
            "refresh_token_lifetime_seconds",
            "idle_timeout_seconds",
            "session_max_lifetime_seconds",
            "mfa_required_methods",
            "password_min_length",
            "theme_name",
            "risk_scoring_enabled",
            "break_glass_max_duration_seconds",
            "metadata",
        ]
        read_only_fields = ["id"]


class IdentityRealmSerializer(serializers.ModelSerializer):
    configuration = RealmConfigurationSerializer(read_only=True)

    class Meta:
        model = IdentityRealm
        fields = [
            "id",
            "tenant_id",
            "realm_name",
            "realm_type",
            "status",
            "issuer_url",
            "jwks_uri",
            "admin_api_url",
            "is_active",
            "mfa_enforced",
            "passkey_enabled",
            "saml_federation_enabled",
            "scim_endpoint",
            "home_region",
            "locale",
            "activated_at",
            "suspended_at",
            "metadata",
            "configuration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "activated_at", "suspended_at", "created_at", "updated_at"]


class IdentityRealmProvisionSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    realm_name = serializers.RegexField(r"^[a-z0-9-]{3,100}$")
    realm_type = serializers.ChoiceField(choices=RealmType.choices)
    display_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    enabled = serializers.BooleanField(default=True)
    access_token_lifetime = serializers.IntegerField(min_value=60, max_value=86400, default=900)
    mfa_methods = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    home_region = serializers.CharField(max_length=50, default="me-central-1")
    locale = serializers.CharField(max_length=10, default="en")


# ---------------------------------------------------------------------------
# Identity Provider (federation)
# ---------------------------------------------------------------------------
class IdentityProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityProvider
        fields = [
            "id",
            "realm",
            "alias",
            "display_name",
            "protocol",
            "enabled",
            "trust_email",
            "store_token",
            "link_only",
            "entity_id",
            "sso_url",
            "slo_url",
            "authorization_url",
            "token_url",
            "userinfo_url",
            "client_id",
            "client_secret_ref",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Service principal / Application client / Secret
# ---------------------------------------------------------------------------
class ServicePrincipalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePrincipal
        fields = [
            "id",
            "name",
            "realm",
            "client_id",
            "is_active",
            "scopes",
            "description",
            "token_lifetime_seconds",
            "last_token_issued_at",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_token_issued_at", "created_at", "updated_at"]


class ApplicationClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationClient
        fields = [
            "id",
            "realm",
            "client_id",
            "name",
            "description",
            "protocol",
            "enabled",
            "public_client",
            "standard_flow_enabled",
            "direct_access_grants_enabled",
            "service_accounts_enabled",
            "redirect_uris",
            "web_origins",
            "root_url",
            "base_url",
            "consent_required",
            "mfa_required",
            "fapi_profile_enabled",
            "smart_on_fhir_enabled",
            "attributes",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicationClientRegisterSerializer(serializers.Serializer):
    realm_id = serializers.UUIDField()
    client_id = serializers.RegexField(r"^[a-zA-Z0-9_-]{3,200}$")
    name = serializers.CharField(max_length=200)
    protocol = serializers.ChoiceField(choices=["oidc", "oauth2", "saml"], default="oidc")
    public_client = serializers.BooleanField(default=False)
    redirect_uris = serializers.ListField(child=serializers.URLField(), default=list)
    web_origins = serializers.ListField(child=serializers.CharField(), default=list)
    root_url = serializers.URLField(required=False, allow_blank=True, default="")
    mfa_required = serializers.BooleanField(default=True)
    fapi_profile_enabled = serializers.BooleanField(default=False)
    smart_on_fhir_enabled = serializers.BooleanField(default=False)


class ClientSecretSerializer(serializers.ModelSerializer):
    """Outbound — never returns the hash or cleartext."""

    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = ClientSecret
        fields = [
            "id",
            "client",
            "secret_hint",
            "created_at",
            "expires_at",
            "revoked_at",
            "last_used_at",
            "created_by",
            "is_active",
        ]
        read_only_fields = fields


class ClientSecretCreateResponseSerializer(serializers.Serializer):
    """Outbound — cleartext returned EXACTLY ONCE at creation/rotation."""

    id = serializers.UUIDField()
    client_id = serializers.CharField()
    cleartext = serializers.CharField()
    secret_hint = serializers.CharField()
    expires_at = serializers.DateTimeField(allow_null=True)
    rotated_at = serializers.DateTimeField()


# ---------------------------------------------------------------------------
# Role / Permission / Assignment
# ---------------------------------------------------------------------------
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            "id",
            "scope",
            "action",
            "resource",
            "description",
            "requires_mfa",
            "requires_approval",
            "policy_bundle_ref",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            "id",
            "realm",
            "name",
            "display_name",
            "description",
            "composite",
            "client_role",
            "client",
            "attributes",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleAssignment
        fields = [
            "id",
            "kind",
            "role",
            "permission",
            "child_role",
            "granted_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Group / Membership
# ---------------------------------------------------------------------------
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            "id",
            "realm",
            "name",
            "path",
            "parent",
            "description",
            "attributes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembership
        fields = [
            "id",
            "group",
            "user_id",
            "membership_expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# User profile / Session / Login audit
# ---------------------------------------------------------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "realm",
            "keycloak_user_id",
            "username",
            "email",
            "email_verified",
            "display_name",
            "given_name",
            "family_name",
            "locale",
            "enabled",
            "mfa_enrolled",
            "mfa_methods",
            "last_login_at",
            "failed_login_count",
            "locked_until",
            "is_locked",
            "attributes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "keycloak_user_id",
            "last_login_at",
            "failed_login_count",
            "locked_until",
            "is_locked",
            "created_at",
            "updated_at",
        ]


class UserProvisionSerializer(serializers.Serializer):
    realm_id = serializers.UUIDField()
    username = serializers.RegexField(r"^[a-zA-Z0-9_.-]{3,200}$")
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    enabled = serializers.BooleanField(default=True)
    email_verified = serializers.BooleanField(default=False)
    attributes = serializers.DictField(required=False, default=dict)


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = [
            "id",
            "user",
            "keycloak_session_id",
            "status",
            "ip_address",
            "user_agent",
            "geo_country",
            "started_at",
            "last_activity_at",
            "expires_at",
            "revoked_at",
            "revoked_reason",
            "risk_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "started_at", "last_activity_at", "revoked_at", "created_at", "updated_at"]


class LoginAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAudit
        fields = [
            "id",
            "user",
            "realm",
            "outcome",
            "username_attempted",
            "ip_address",
            "user_agent",
            "mfa_method",
            "session",
            "failure_reason",
            "details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Device / WebAuthn / BreakGlass
# ---------------------------------------------------------------------------
class DeviceRegistrationSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeviceRegistration
        fields = [
            "id",
            "user",
            "device_id",
            "name",
            "device_type",
            "platform",
            "os_version",
            "user_agent",
            "fingerprint",
            "trusted",
            "last_used_at",
            "revoked_at",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "device_id", "last_used_at", "revoked_at", "is_active", "created_at", "updated_at"]


class WebAuthnCredentialSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = WebAuthnCredential
        fields = [
            "id",
            "user",
            "device",
            "credential_id",
            "attestation_format",
            "aaguid",
            "sign_count",
            "transports",
            "user_verification",
            "label",
            "last_used_at",
            "revoked_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        # NEVER expose public_key via API — it's stored for future assertions
        read_only_fields = ["id", "last_used_at", "revoked_at", "is_active", "created_at", "updated_at"]


class BreakGlassAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakGlassAccess
        fields = [
            "id",
            "user",
            "realm",
            "reason",
            "justification",
            "target_resource",
            "target_action",
            "status",
            "requested_at",
            "approved_by",
            "approved_at",
            "second_approver",
            "activated_at",
            "expires_at",
            "revoked_at",
            "post_review_notes",
            "post_review_completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "approved_by",
            "approved_at",
            "second_approver",
            "activated_at",
            "expires_at",
            "revoked_at",
            "requested_at",
            "post_review_completed_at",
            "created_at",
            "updated_at",
        ]


class BreakGlassRequestSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    realm_id = serializers.UUIDField()
    reason = serializers.ChoiceField(choices=BreakGlassReason.choices)
    justification = serializers.CharField(min_length=10, max_length=2000)
    target_resource = serializers.CharField(max_length=300)
    target_action = serializers.CharField(max_length=100)


class BreakGlassApproveSerializer(serializers.Serializer):
    approver = serializers.CharField(max_length=255)
    second_approver = serializers.CharField(max_length=255)


class BreakGlassActivateSerializer(serializers.Serializer):
    duration_seconds = serializers.IntegerField(min_value=60, max_value=86400, required=False)


# ---------------------------------------------------------------------------
# Health / Metrics
# ---------------------------------------------------------------------------
class IdentityHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    realm_count = serializers.IntegerField()
    active_realm_count = serializers.IntegerField()
    active_session_count = serializers.IntegerField()
    keycloak_enabled = serializers.BooleanField()


class TokenValidateRequestSerializer(serializers.Serializer):
    token = serializers.CharField()
    audience = serializers.CharField(required=False, allow_blank=True)


class TokenValidateResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    subject = serializers.CharField(allow_blank=True, required=False)
    issuer = serializers.CharField(allow_blank=True, required=False)
    audience = serializers.CharField(allow_blank=True, required=False)
    expires_at = serializers.IntegerField(required=False)
    scope = serializers.CharField(allow_blank=True, required=False)
