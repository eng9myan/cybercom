"""CyIdentity admin. Program 2.1: full CRUD + readonly for audit tables."""
from django.contrib import admin

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
    RealmConfiguration,
    Role,
    RoleAssignment,
    ServicePrincipal,
    UserProfile,
    UserSession,
    WebAuthnCredential,
)


@admin.register(IdentityRealm)
class IdentityRealmAdmin(admin.ModelAdmin):
    list_display = ["realm_name", "realm_type", "status", "is_active", "mfa_enforced", "passkey_enabled", "home_region"]
    list_filter = ["realm_type", "status", "is_active", "mfa_enforced"]
    search_fields = ["realm_name", "tenant_id"]
    readonly_fields = ["id", "created_at", "updated_at", "activated_at", "suspended_at"]


@admin.register(RealmConfiguration)
class RealmConfigurationAdmin(admin.ModelAdmin):
    list_display = ["realm", "access_token_lifetime_seconds", "session_max_lifetime_seconds", "risk_scoring_enabled"]
    search_fields = ["realm__realm_name"]


@admin.register(IdentityProvider)
class IdentityProviderAdmin(admin.ModelAdmin):
    list_display = ["alias", "realm", "protocol", "enabled", "trust_email"]
    list_filter = ["protocol", "enabled"]
    search_fields = ["alias", "display_name"]


@admin.register(ServicePrincipal)
class ServicePrincipalAdmin(admin.ModelAdmin):
    list_display = ["name", "client_id", "realm", "is_active"]
    list_filter = ["is_active", "realm"]
    search_fields = ["name", "client_id"]


@admin.register(ApplicationClient)
class ApplicationClientAdmin(admin.ModelAdmin):
    list_display = ["client_id", "name", "realm", "protocol", "enabled", "mfa_required", "fapi_profile_enabled", "smart_on_fhir_enabled"]
    list_filter = ["protocol", "enabled", "fapi_profile_enabled", "smart_on_fhir_enabled"]
    search_fields = ["client_id", "name"]


@admin.register(ClientSecret)
class ClientSecretAdmin(admin.ModelAdmin):
    list_display = ["client", "secret_hint", "created_at", "expires_at", "revoked_at"]
    list_filter = ["revoked_at"]
    search_fields = ["client__client_id"]
    readonly_fields = ["id", "secret_hash", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["scope", "action", "resource", "requires_mfa", "requires_approval"]
    list_filter = ["scope", "requires_mfa", "requires_approval"]
    search_fields = ["scope", "action", "resource"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "realm", "client_role", "composite", "is_default"]
    list_filter = ["client_role", "composite", "is_default"]
    search_fields = ["name", "display_name"]


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ["role", "kind", "permission", "child_role", "granted_by", "created_at"]
    list_filter = ["kind"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "path", "realm", "parent"]
    search_fields = ["name", "path"]


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ["group", "user_id", "membership_expires_at", "created_at"]
    list_filter = ["group__realm"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "realm", "enabled", "mfa_enrolled", "is_locked", "last_login_at"]
    list_filter = ["enabled", "mfa_enrolled", "locale", "realm"]
    search_fields = ["username", "email", "display_name", "keycloak_user_id"]
    readonly_fields = ["id", "keycloak_user_id", "created_at", "updated_at", "last_login_at"]


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "ip_address", "started_at", "last_activity_at", "expires_at", "risk_score"]
    list_filter = ["status", "geo_country"]
    search_fields = ["user__username", "keycloak_session_id"]
    readonly_fields = ["id", "started_at", "last_activity_at", "revoked_at", "created_at", "updated_at"]


@admin.register(LoginAudit)
class LoginAuditAdmin(admin.ModelAdmin):
    list_display = ["outcome", "username_attempted", "realm", "user", "mfa_method", "created_at"]
    list_filter = ["outcome", "mfa_method", "realm"]
    search_fields = ["username_attempted", "user__username"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DeviceRegistration)
class DeviceRegistrationAdmin(admin.ModelAdmin):
    list_display = ["name", "device_type", "user", "trusted", "revoked_at", "last_used_at"]
    list_filter = ["device_type", "trusted", "revoked_at"]
    search_fields = ["name", "user__username", "fingerprint"]


@admin.register(WebAuthnCredential)
class WebAuthnCredentialAdmin(admin.ModelAdmin):
    list_display = ["label", "user", "attestation_format", "aaguid", "last_used_at", "revoked_at"]
    list_filter = ["attestation_format", "user_verification"]
    search_fields = ["label", "credential_id", "user__username"]
    readonly_fields = ["id", "credential_id", "public_key", "sign_count", "created_at", "updated_at", "last_used_at"]


@admin.register(BreakGlassAccess)
class BreakGlassAccessAdmin(admin.ModelAdmin):
    list_display = ["user", "realm", "reason", "status", "target_resource", "approved_by", "second_approver", "expires_at"]
    list_filter = ["status", "reason", "realm"]
    search_fields = ["user__username", "approved_by", "target_resource"]
    readonly_fields = ["id", "requested_at", "approved_at", "activated_at", "expires_at", "revoked_at", "created_at", "updated_at"]
