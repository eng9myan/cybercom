"""
CyIdentity platform models. ADR-0005 (IAM Strategy), ADR-0017 (CyIdentity Product),
ADR-0035 (Keycloak 24 finalization).

This module is the control-plane mirror of the Keycloak realm state.
The actual user directory, credentials, sessions, and token signing live in
Keycloak 24; rows in this module describe the CyberCom-side metadata
(realm lifecycle, client registry, role/permission catalog, break-glass
access records, audit hooks).

17 domain models per Program 2.1 spec:
  IdentityRealm, RealmConfiguration, IdentityProvider,
  ServicePrincipal, ApplicationClient, ClientSecret,
  Role, Permission, RoleAssignment,
  Group, GroupMembership,
  UserProfile, UserSession, LoginAudit,
  DeviceRegistration, WebAuthnCredential,
  BreakGlassAccess
"""
from __future__ import annotations

import uuid
from django.db import models
from django.utils import timezone
from platform.common.models import BaseModel, PlatformModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class RealmType(models.TextChoices):
    WORKFORCE = "workforce", "Workforce"
    CUSTOMER = "customer", "Customer (per-tenant)"
    CITIZEN = "citizen", "Citizen (per-jurisdiction)"
    PARTNER = "partner", "Partner (B2B)"
    WORKLOAD = "workload", "Workload (services/jobs)"


class RealmStatus(models.TextChoices):
    PENDING = "pending", "Pending Provisioning"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    DECOMMISSIONED = "decommissioned", "Decommissioned"


class ClientProtocol(models.TextChoices):
    OIDC = "oidc", "OpenID Connect"
    OAUTH2 = "oauth2", "OAuth 2.1"
    SAML = "saml", "SAML 2.0"
    SERVICE_ACCOUNT = "service_account", "Service Account (M2M)"


class MFAMethod(models.TextChoices):
    NONE = "none", "None"
    TOTP = "totp", "TOTP"
    WEBAUTHN = "webauthn", "WebAuthn / Passkey"
    SMS = "sms", "SMS OTP (fallback only)"
    EMAIL = "email", "Email OTP (fallback only)"
    PUSH = "push", "Push Notification"


class SessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"
    IDLE_TIMEOUT = "idle_timeout", "Idle Timeout"


class BreakGlassStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    APPROVED = "approved", "Approved"
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"
    DENIED = "denied", "Denied"


class BreakGlassReason(models.TextChoices):
    CLINICAL = "clinical", "Clinical Emergency"
    SECURITY = "security", "Security Incident"
    OPERATIONAL = "operational", "Operational Outage"
    COMPLIANCE = "compliance", "Compliance / Legal"


# ---------------------------------------------------------------------------
# 1. IdentityRealm — maps tenant to Keycloak realm
# ---------------------------------------------------------------------------
class IdentityRealm(PlatformModel):
    """
    One Keycloak realm per CyberCom tenant.
    ADR-0017 §5.2: per-tenant realm isolation.
    ADR-0035 §5.3: realm map by population type.
    """
    tenant_id = models.UUIDField(unique=True, db_index=True)
    realm_name = models.CharField(max_length=100, unique=True)
    realm_type = models.CharField(max_length=20, choices=RealmType.choices)
    status = models.CharField(max_length=20, choices=RealmStatus.choices, default=RealmStatus.PENDING)
    issuer_url = models.URLField(max_length=500)
    jwks_uri = models.URLField(max_length=500)
    admin_api_url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    mfa_enforced = models.BooleanField(default=True)
    passkey_enabled = models.BooleanField(default=True)
    saml_federation_enabled = models.BooleanField(default=False)
    scim_endpoint = models.URLField(blank=True)
    home_region = models.CharField(max_length=50, default="me-central-1")
    locale = models.CharField(max_length=10, default="en")
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_identity_realms"
        ordering = ["realm_name"]
        indexes = [
            models.Index(fields=["realm_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"Realm({self.realm_name}, {self.realm_type})"

    def activate(self) -> None:
        self.status = RealmStatus.ACTIVE
        self.is_active = True
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "is_active", "activated_at", "updated_at"])

    def suspend(self) -> None:
        self.status = RealmStatus.SUSPENDED
        self.is_active = False
        self.suspended_at = timezone.now()
        self.save(update_fields=["status", "is_active", "suspended_at", "updated_at"])

    def decommission(self) -> None:
        self.status = RealmStatus.DECOMMISSIONED
        self.is_active = False
        self.save(update_fields=["status", "is_active", "updated_at"])


# ---------------------------------------------------------------------------
# 2. RealmConfiguration — per-realm tunables
# ---------------------------------------------------------------------------
class RealmConfiguration(PlatformModel):
    """Realm-level tunables: token lifetime, theme, MFA policy, branding."""
    realm = models.OneToOneField(IdentityRealm, on_delete=models.CASCADE, related_name="configuration")
    access_token_lifetime_seconds = models.PositiveIntegerField(default=900)  # 15 min
    refresh_token_lifetime_seconds = models.PositiveIntegerField(default=1800)  # 30 min
    idle_timeout_seconds = models.PositiveIntegerField(default=1800)  # 30 min
    session_max_lifetime_seconds = models.PositiveIntegerField(default=28800)  # 8 h
    mfa_required_methods = models.JSONField(default=list, blank=True)  # list of MFAMethod values
    password_min_length = models.PositiveIntegerField(default=12)
    theme_name = models.CharField(max_length=100, default="cybercom-default")
    login_theme_vars = models.JSONField(default=dict, blank=True)  # CSS design tokens
    risk_scoring_enabled = models.BooleanField(default=True)
    break_glass_max_duration_seconds = models.PositiveIntegerField(default=3600)  # 1 h
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_realm_configurations"

    def __str__(self) -> str:
        return f"Config({self.realm.realm_name})"


# ---------------------------------------------------------------------------
# 3. IdentityProvider — federation partners
# ---------------------------------------------------------------------------
class IdentityProvider(PlatformModel):
    """
    External IdP federated into a realm (SAML/OIDC).
    ADR-0017 §5.2: workforce federates to corporate IdP, customer to tenant IdP,
    citizen to national eID.
    """
    realm = models.ForeignKey(IdentityRealm, on_delete=models.CASCADE, related_name="identity_providers")
    alias = models.SlugField(max_length=100)
    display_name = models.CharField(max_length=200)
    protocol = models.CharField(max_length=20, choices=ClientProtocol.choices)
    enabled = models.BooleanField(default=True)
    trust_email = models.BooleanField(default=False)
    store_token = models.BooleanField(default=False)
    link_only = models.BooleanField(default=False)
    # SAML
    entity_id = models.CharField(max_length=500, blank=True)
    sso_url = models.URLField(blank=True)
    slo_url = models.URLField(blank=True)
    x509_cert = models.TextField(blank=True)
    # OIDC
    authorization_url = models.URLField(blank=True)
    token_url = models.URLField(blank=True)
    userinfo_url = models.URLField(blank=True)
    client_id = models.CharField(max_length=200, blank=True)
    client_secret_ref = models.CharField(max_length=200, blank=True)  # vault path
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_identity_providers"
        unique_together = [("realm", "alias")]
        indexes = [
            models.Index(fields=["realm", "enabled"]),
        ]

    def __str__(self) -> str:
        return f"IdP({self.realm.realm_name}/{self.alias})"


# ---------------------------------------------------------------------------
# 4. ServicePrincipal — M2M workload identity
# ---------------------------------------------------------------------------
class ServicePrincipal(PlatformModel):
    """
    Machine-to-machine service account.
    ADR-0017 §5.4: workload identity for out-of-mesh services.
    """
    name = models.CharField(max_length=200)
    realm = models.ForeignKey(IdentityRealm, on_delete=models.PROTECT, related_name="service_principals")
    client_id = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    scopes = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    token_lifetime_seconds = models.PositiveIntegerField(default=300)  # 5 min
    last_token_issued_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_service_principals"
        indexes = [
            models.Index(fields=["realm", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"ServicePrincipal({self.name})"


# ---------------------------------------------------------------------------
# 5. ApplicationClient — OAuth/OIDC/SAML application registration
# ---------------------------------------------------------------------------
class ApplicationClient(PlatformModel):
    """
    Registered OAuth 2.1 / OIDC client (frontend, mobile, partner app).
    ADR-0017 §5.3: apps registered per tenant.
    """
    realm = models.ForeignKey(IdentityRealm, on_delete=models.CASCADE, related_name="clients")
    client_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    protocol = models.CharField(max_length=20, choices=ClientProtocol.choices, default=ClientProtocol.OIDC)
    enabled = models.BooleanField(default=True)
    public_client = models.BooleanField(default=False)  # PKCE for native/SPA
    standard_flow_enabled = models.BooleanField(default=True)
    direct_access_grants_enabled = models.BooleanField(default=False)
    service_accounts_enabled = models.BooleanField(default=False)
    redirect_uris = models.JSONField(default=list, blank=True)
    web_origins = models.JSONField(default=list, blank=True)
    root_url = models.URLField(blank=True)
    base_url = models.URLField(blank=True)
    consent_required = models.BooleanField(default=False)
    mfa_required = models.BooleanField(default=True)
    fapi_profile_enabled = models.BooleanField(default=False)
    smart_on_fhir_enabled = models.BooleanField(default=False)
    attributes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_application_clients"
        indexes = [
            models.Index(fields=["realm", "enabled"]),
        ]

    def __str__(self) -> str:
        return f"Client({self.client_id})"


# ---------------------------------------------------------------------------
# 6. ClientSecret — rotating secrets for confidential clients
# ---------------------------------------------------------------------------
class ClientSecret(BaseModel):
    """
    Rotating client secret. ADR-0035 §5.2 — secret rotation quarterly.
    Only the hash is stored; cleartext is returned exactly once at creation.
    """
    client = models.ForeignKey(ApplicationClient, on_delete=models.CASCADE, related_name="secrets")
    secret_hash = models.CharField(max_length=128)
    secret_hint = models.CharField(max_length=8, blank=True)  # last 4 chars for UI display
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "platform_client_secrets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "revoked_at"]),
        ]

    def __str__(self) -> str:
        return f"ClientSecret({self.client.client_id}, …{self.secret_hint})"

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at <= timezone.now():
            return False
        return True

    def revoke(self) -> None:
        self.revoked_at = timezone.now()
        self.save(update_fields=["revoked_at", "updated_at"])


# ---------------------------------------------------------------------------
# 7. Role — RBAC role
# ---------------------------------------------------------------------------
class Role(PlatformModel):
    """
    RBAC role within a realm. ADR-0005 hybrid RBAC+ABAC; roles are coarse,
    fine-grained authz lives in the policy engine.
    """
    realm = models.ForeignKey(IdentityRealm, on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    composite = models.BooleanField(default=False)
    client_role = models.BooleanField(default=False)  # client-scoped vs realm-scoped
    client = models.ForeignKey(ApplicationClient, on_delete=models.CASCADE, null=True, blank=True, related_name="roles")
    attributes = models.JSONField(default=dict, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "platform_roles"
        unique_together = [("realm", "name", "client")]
        indexes = [
            models.Index(fields=["realm", "client_role"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["realm", "name"],
                condition=models.Q(client__isnull=True),
                name="unique_realm_role_global",
            )
        ]

    def __str__(self) -> str:
        scope = self.client.client_id if self.client_id else "realm"
        return f"Role({self.realm.realm_name}/{self.name}@{scope})"


# ---------------------------------------------------------------------------
# 8. Permission — fine-grained permission catalog
# ---------------------------------------------------------------------------
class Permission(PlatformModel):
    """Permission catalog entry. Bound to roles via RoleAssignment."""
    scope = models.CharField(max_length=100)  # e.g. "cymed", "cycom", "platform"
    action = models.CharField(max_length=50)  # e.g. "read", "write", "delete", "approve"
    resource = models.CharField(max_length=100)  # e.g. "patient", "ledger", "role"
    description = models.TextField(blank=True)
    requires_mfa = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    policy_bundle_ref = models.CharField(max_length=255, blank=True)  # OPA bundle path

    class Meta:
        db_table = "platform_permissions"
        unique_together = [("scope", "action", "resource")]
        indexes = [
            models.Index(fields=["scope", "action"]),
        ]

    def __str__(self) -> str:
        return f"{self.scope}:{self.action}:{self.resource}"


# ---------------------------------------------------------------------------
# 9. RoleAssignment — many-to-many role→permission + role inheritance
# ---------------------------------------------------------------------------
class RoleAssignment(PlatformModel):
    """
    Assignment of a permission to a role, or a child role to a parent role.
    """
    ASSIGNMENT_KIND_CHOICES = [
        ("permission", "Permission"),
        ("composite", "Composite Role"),
    ]
    kind = models.CharField(max_length=20, choices=ASSIGNMENT_KIND_CHOICES, default="permission")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, null=True, blank=True, related_name="assignments")
    child_role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True, related_name="parent_assignments")
    granted_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "platform_role_assignments"
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(kind="permission", permission__isnull=False, child_role__isnull=True)
                    | models.Q(kind="composite", child_role__isnull=False, permission__isnull=True)
                ),
                name="role_assignment_kind_xor",
            ),
        ]

    def __str__(self) -> str:
        if self.kind == "permission" and self.permission_id:
            return f"RoleAssignment({self.role.name} → {self.permission})"
        return f"RoleAssignment({self.role.name} ⊇ {self.child_role.name if self.child_role_id else '?'})"


# ---------------------------------------------------------------------------
# 10. Group — realm group (collection of users + roles)
# ---------------------------------------------------------------------------
class Group(PlatformModel):
    """Keycloak-style group for bulk role assignment and ABAC attributes."""
    realm = models.ForeignKey(IdentityRealm, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=200)
    path = models.CharField(max_length=500, db_index=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    description = models.TextField(blank=True)
    attributes = models.JSONField(default=dict, blank=True)  # ABAC attribute source

    class Meta:
        db_table = "platform_identity_groups"
        unique_together = [("realm", "path")]
        indexes = [
            models.Index(fields=["realm", "parent"]),
        ]

    def __str__(self) -> str:
        return f"Group({self.path})"


# ---------------------------------------------------------------------------
# 11. GroupMembership — user→group
# ---------------------------------------------------------------------------
class GroupMembership(BaseModel):
    """A user's membership in a group (one user can belong to many groups)."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user_id = models.UUIDField(db_index=True)  # Keycloak user sub
    membership_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform_group_memberships"
        unique_together = [("group", "user_id")]

    def __str__(self) -> str:
        return f"Membership({self.user_id} ⊂ {self.group.path})"


# ---------------------------------------------------------------------------
# 12. UserProfile — control-plane mirror of Keycloak user
# ---------------------------------------------------------------------------
class UserProfile(BaseModel):
    """
    CyberCom-side user profile metadata.
    Authoritative credential and authentication state lives in Keycloak;
    this row holds CyberCom attributes (display name, locale, status, attributes).
    """
    realm = models.ForeignKey(IdentityRealm, on_delete=models.CASCADE, related_name="users")
    keycloak_user_id = models.UUIDField(unique=True, db_index=True)  # Keycloak `sub`
    username = models.CharField(max_length=200)
    email = models.EmailField()
    email_verified = models.BooleanField(default=False)
    display_name = models.CharField(max_length=300, blank=True)
    given_name = models.CharField(max_length=150, blank=True)
    family_name = models.CharField(max_length=150, blank=True)
    locale = models.CharField(max_length=10, default="en")
    enabled = models.BooleanField(default=True)
    mfa_enrolled = models.BooleanField(default=False)
    mfa_methods = models.JSONField(default=list, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    failed_login_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_user_profiles"
        unique_together = [("realm", "username")]
        indexes = [
            models.Index(fields=["realm", "enabled"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return f"User({self.username}@{self.realm.realm_name})"

    def record_login(self) -> None:
        self.last_login_at = timezone.now()
        self.failed_login_count = 0
        self.save(update_fields=["last_login_at", "failed_login_count", "updated_at"])

    def record_failed_login(self, lock_threshold: int = 5) -> None:
        self.failed_login_count += 1
        if self.failed_login_count >= lock_threshold:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=15)
            self.save(update_fields=["failed_login_count", "locked_until", "updated_at"])
        else:
            self.save(update_fields=["failed_login_count", "updated_at"])

    @property
    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > timezone.now()


# ---------------------------------------------------------------------------
# 13. UserSession — session tracking + revocation
# ---------------------------------------------------------------------------
class UserSession(BaseModel):
    """Active/expired/revoked session. Mirrored from Keycloak session list."""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="sessions")
    keycloak_session_id = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.ACTIVE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    geo_country = models.CharField(max_length=2, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    last_activity_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=200, blank=True)
    risk_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    class Meta:
        db_table = "platform_user_sessions"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self) -> str:
        return f"Session({self.user.username}, {self.status})"

    def revoke(self, reason: str = "user_request") -> None:
        if reason == "idle_timeout":
            self.status = SessionStatus.IDLE_TIMEOUT
        else:
            self.status = SessionStatus.REVOKED
        self.revoked_at = timezone.now()
        self.revoked_reason = reason
        self.save(update_fields=["status", "revoked_at", "revoked_reason", "updated_at"])

    def touch(self) -> None:
        self.last_activity_at = timezone.now()
        self.save(update_fields=["last_activity_at", "updated_at"])


# ---------------------------------------------------------------------------
# 14. LoginAudit — authN event log
# ---------------------------------------------------------------------------
class LoginAudit(BaseModel):
    """Per-login audit record. Streams to platform_audit_logs in production."""
    OUTCOME_CHOICES = [
        ("success", "Success"),
        ("failure", "Failure"),
        ("mfa_challenge", "MFA Challenge"),
        ("mfa_failure", "MFA Failure"),
        ("locked", "Account Locked"),
        ("break_glass", "Break Glass"),
    ]
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="login_events")
    realm = models.ForeignKey(IdentityRealm, on_delete=models.CASCADE, related_name="login_events")
    outcome = models.CharField(max_length=30, choices=OUTCOME_CHOICES, db_index=True)
    username_attempted = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    mfa_method = models.CharField(max_length=30, blank=True)
    session = models.ForeignKey(UserSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="login_events")
    failure_reason = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_login_audits"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["realm", "outcome"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"LoginAudit({self.outcome}, {self.username_attempted})"


# ---------------------------------------------------------------------------
# 15. DeviceRegistration — bound device for MFA / passkey / mobile sessions
# ---------------------------------------------------------------------------
class DeviceRegistration(BaseModel):
    """A device the user has registered for MFA or persistent session."""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="devices")
    device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=50)  # mobile, desktop, hardware_key, browser
    platform = models.CharField(max_length=50, blank=True)  # iOS, Android, Windows, …
    os_version = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)
    fingerprint = models.CharField(max_length=128, blank=True)
    trusted = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_device_registrations"
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
        ]

    def __str__(self) -> str:
        return f"Device({self.name}, {self.device_type})"

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


# ---------------------------------------------------------------------------
# 16. WebAuthnCredential — registered passkey / security key
# ---------------------------------------------------------------------------
class WebAuthnCredential(BaseModel):
    """
    WebAuthn / Passkey credential metadata.
    Private key material NEVER stored; only credential ID + public key + counters.
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="webauthn_credentials")
    device = models.ForeignKey(DeviceRegistration, on_delete=models.SET_NULL, null=True, blank=True, related_name="webauthn_credentials")
    credential_id = models.CharField(max_length=512, unique=True, db_index=True)
    public_key = models.TextField()  # COSE-encoded base64
    attestation_format = models.CharField(max_length=50, blank=True)
    aaguid = models.CharField(max_length=64, blank=True)
    sign_count = models.PositiveBigIntegerField(default=0)
    transports = models.JSONField(default=list, blank=True)  # ["usb","nfc","ble","internal"]
    user_verification = models.CharField(max_length=20, default="preferred")
    label = models.CharField(max_length=200, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform_webauthn_credentials"
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
        ]

    def __str__(self) -> str:
        return f"WebAuthn({self.label or self.credential_id[:16]})"

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


# ---------------------------------------------------------------------------
# 17. BreakGlassAccess — emergency access with audit + auto-expiry
# ---------------------------------------------------------------------------
class BreakGlassAccess(BaseModel):
    """
    Time-boxed emergency access. ADR-0017 §7.3 Risk-8 — mandatory dual-approval,
    automatic expiration, audit logged, 24-hour post-review required.
    """
    user = models.ForeignKey(UserProfile, on_delete=models.PROTECT, related_name="break_glass_accesses")
    realm = models.ForeignKey(IdentityRealm, on_delete=models.PROTECT, related_name="break_glass_accesses")
    reason = models.CharField(max_length=30, choices=BreakGlassReason.choices)
    justification = models.TextField()
    target_resource = models.CharField(max_length=300)
    target_action = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=BreakGlassStatus.choices, default=BreakGlassStatus.REQUESTED)
    requested_at = models.DateTimeField(default=timezone.now)
    approved_by = models.CharField(max_length=255, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    second_approver = models.CharField(max_length=255, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    post_review_notes = models.TextField(blank=True)
    post_review_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform_break_glass_accesses"
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self) -> str:
        return f"BreakGlass({self.user.username}, {self.reason}, {self.status})"

    def approve(self, approver: str, second_approver: str = "") -> None:
        self.status = BreakGlassStatus.APPROVED
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.second_approver = second_approver
        self.save(update_fields=["status", "approved_by", "approved_at", "second_approver", "updated_at"])

    def activate(self, duration_seconds: int = 3600) -> None:
        self.status = BreakGlassStatus.ACTIVE
        self.activated_at = timezone.now()
        self.expires_at = self.activated_at + timezone.timedelta(seconds=duration_seconds)
        self.save(update_fields=["status", "activated_at", "expires_at", "updated_at"])

    def revoke(self) -> None:
        self.status = BreakGlassStatus.REVOKED
        self.revoked_at = timezone.now()
        self.save(update_fields=["status", "revoked_at", "updated_at"])

    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= timezone.now()
