"""
CyIdentity test suite. Program 2.1 — coverage target 90%.
Tests cover:
  - Model invariants for all 17 domain models
  - Service layer (RealmService, ClientService, UserProvisioningService,
    RoleSyncService, SessionService, BreakGlassService, AuditService)
  - Token validation + JWKS cache graceful degradation
  - All REST endpoints via DRF APIClient
  - Signals lifecycle hooks
  - Celery tasks
  - Permission classes
"""

import uuid
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from platform.cyidentity.models import (
    ApplicationClient,
    BreakGlassReason,
    BreakGlassStatus,
    ClientProtocol,
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
    SessionStatus,
    UserProfile,
    UserSession,
    WebAuthnCredential,
)
from platform.cyidentity.services import (
    BreakGlassService,
    ClientService,
    IdentityMetrics,
    JWKSCache,
    KeycloakAdminClient,
    RealmService,
    RoleSyncService,
    SessionService,
    TokenValidationError,
    TokenValidator,
    UserProvisioningService,
    hash_client_secret,
    metrics,
    render_prometheus,
    verify_client_secret,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def realm(db, tenant_id):
    return IdentityRealm.objects.create(
        tenant_id=tenant_id,
        realm_name="acme-test",
        realm_type=RealmType.CUSTOMER,
        status=RealmStatus.PENDING,
        issuer_url="http://localhost:8080/realms/acme-test",
        jwks_uri="http://localhost:8080/realms/acme-test/protocol/openid-connect/certs",
        admin_api_url="http://localhost:8080/admin/realms/acme-test",
    )


@pytest.fixture
def active_realm(realm):
    realm.activate()
    realm.refresh_from_db()
    return realm


@pytest.fixture
def realm_config(active_realm):
    return RealmConfiguration.objects.create(realm=active_realm, mfa_required_methods=["webauthn"])


@pytest.fixture
def fake_kc():
    """In-memory Keycloak admin client; no network."""
    return KeycloakAdminClient()


@pytest.fixture
def admin_client():
    return APIClient()


# ── Realm lifecycle ──────────────────────────────────────────────────────


class TestIdentityRealm:
    def test_create_realm_pending(self, db, tenant_id):
        realm = IdentityRealm.objects.create(
            tenant_id=tenant_id,
            realm_name="r1",
            realm_type=RealmType.CUSTOMER,
            issuer_url="http://x",
            jwks_uri="http://x/jwks",
            admin_api_url="http://x/admin",
        )
        assert realm.status == RealmStatus.PENDING
        assert realm.is_active is True

    def test_activate(self, realm):
        realm.activate()
        realm.refresh_from_db()
        assert realm.status == RealmStatus.ACTIVE
        assert realm.activated_at is not None
        assert realm.is_active is True

    def test_suspend(self, active_realm):
        active_realm.suspend()
        active_realm.refresh_from_db()
        assert active_realm.status == RealmStatus.SUSPENDED
        assert active_realm.is_active is False
        assert active_realm.suspended_at is not None

    def test_decommission(self, active_realm):
        active_realm.decommission()
        active_realm.refresh_from_db()
        assert active_realm.status == RealmStatus.DECOMMISSIONED
        assert active_realm.is_active is False

    def test_str(self, realm):
        assert "acme-test" in str(realm)

    def test_realm_name_unique(self, realm, tenant_id):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            IdentityRealm.objects.create(
                tenant_id=tenant_id,
                realm_name="acme-test",
                realm_type=RealmType.CUSTOMER,
                issuer_url="http://x",
                jwks_uri="http://x/jwks",
                admin_api_url="http://x/admin",
            )


# ── Configuration ─────────────────────────────────────────────────────────


class TestRealmConfiguration:
    def test_defaults(self, active_realm):
        cfg = RealmConfiguration.objects.create(realm=active_realm)
        assert cfg.access_token_lifetime_seconds == 900
        assert cfg.break_glass_max_duration_seconds == 3600
        assert cfg.mfa_required_methods == []

    def test_str(self, realm_config):
        assert "acme-test" in str(realm_config)


# ── Identity Provider federation ─────────────────────────────────────────


class TestIdentityProvider:
    def test_unique_alias_per_realm(self, active_realm):
        IdentityProvider.objects.create(
            realm=active_realm, alias="corporate", display_name="Corp", protocol="oidc"
        )
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            IdentityProvider.objects.create(
                realm=active_realm, alias="corporate", display_name="Dup", protocol="oidc"
            )

    def test_different_aliases_ok(self, active_realm):
        IdentityProvider.objects.create(
            realm=active_realm, alias="a", display_name="A", protocol="oidc"
        )
        IdentityProvider.objects.create(
            realm=active_realm, alias="b", display_name="B", protocol="saml"
        )
        assert IdentityProvider.objects.filter(realm=active_realm).count() == 2


# ── Service principal ─────────────────────────────────────────────────────


class TestServicePrincipal:
    def test_create(self, active_realm):
        sp = ServicePrincipal.objects.create(
            name="etl", realm=active_realm, client_id="etl-svc", scopes=["read"]
        )
        assert sp.is_active is True
        assert "etl" in str(sp)

    def test_inactive(self, active_realm):
        sp = ServicePrincipal.objects.create(
            name="x", realm=active_realm, client_id="x", is_active=False
        )
        assert sp.is_active is False


# ── Application client + secret ──────────────────────────────────────────


class TestApplicationClient:
    def test_create_oidc(self, active_realm):
        c = ApplicationClient.objects.create(
            realm=active_realm,
            client_id="web",
            name="Web",
            protocol=ClientProtocol.OIDC,
            public_client=True,
            redirect_uris=["http://app/cb"],
        )
        assert c.public_client is True
        assert c.protocol == ClientProtocol.OIDC

    def test_unique_client_id(self, active_realm):
        ApplicationClient.objects.create(realm=active_realm, client_id="dup", name="A")
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            ApplicationClient.objects.create(realm=active_realm, client_id="dup", name="B")


class TestClientSecret:
    def test_hash_and_verify(self):
        s = "super-secret-value-12345"
        h = hash_client_secret(s)
        assert verify_client_secret(s, h) is True
        assert verify_client_secret("wrong", h) is False

    def test_create(self, active_realm):
        c = ApplicationClient.objects.create(realm=active_realm, client_id="x", name="X")
        cs = ClientSecret.objects.create(
            tenant_id=active_realm.tenant_id,
            client=c,
            secret_hash=hash_client_secret("cleartext-abc"),
            secret_hint="cabc",
        )
        assert cs.is_active is True
        assert "cabc" in str(cs)

    def test_revoke(self, active_realm):
        c = ApplicationClient.objects.create(realm=active_realm, client_id="x", name="X")
        cs = ClientSecret.objects.create(
            tenant_id=active_realm.tenant_id, client=c, secret_hash="h", secret_hint="abcd"
        )
        cs.revoke()
        cs.refresh_from_db()
        assert cs.is_active is False
        assert cs.revoked_at is not None

    def test_expired(self, active_realm):
        c = ApplicationClient.objects.create(realm=active_realm, client_id="x", name="X")
        cs = ClientSecret.objects.create(
            tenant_id=active_realm.tenant_id,
            client=c,
            secret_hash="h",
            secret_hint="abcd",
            expires_at=timezone.now() - timezone.timedelta(seconds=10),
        )
        assert cs.is_active is False


# ── Role / Permission ────────────────────────────────────────────────────


class TestRoleAndPermission:
    def test_unique_permission_triplet(self, db):
        Permission.objects.create(scope="s", action="a", resource="r")
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Permission.objects.create(scope="s", action="a", resource="r")

    def test_role_unique_in_realm(self, active_realm):
        Role.objects.create(realm=active_realm, name="admin")
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Role.objects.create(realm=active_realm, name="admin")

    def test_role_assignment_xor_constraint(self, active_realm):
        role = Role.objects.create(realm=active_realm, name="admin")
        perm = Permission.objects.create(scope="s", action="a", resource="r")
        # Both permission AND child_role set → constraint violation
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            RoleAssignment.objects.create(
                role=role,
                permission=perm,
                child_role=role,
                kind="composite",
            )

    def test_role_assignment_permission_only(self, active_realm):
        role = Role.objects.create(realm=active_realm, name="admin")
        perm = Permission.objects.create(scope="s", action="a", resource="r")
        ra = RoleAssignment.objects.create(
            role=role,
            permission=perm,
            kind="permission",
        )
        assert ra.role_id == role.id
        assert ra.permission_id == perm.id

    def test_role_str(self, active_realm):
        role = Role.objects.create(realm=active_realm, name="admin")
        assert "admin" in str(role)


# ── Group / Membership ───────────────────────────────────────────────────


class TestGroupAndMembership:
    def test_group_hierarchy(self, active_realm):
        parent = Group.objects.create(realm=active_realm, name="root", path="/root")
        child = Group.objects.create(
            realm=active_realm, name="leaf", path="/root/leaf", parent=parent
        )
        assert child.parent_id == parent.id
        assert child in parent.children.all()

    def test_group_membership_unique(self, active_realm):
        g = Group.objects.create(realm=active_realm, name="g", path="/g")
        GroupMembership.objects.create(
            tenant_id=active_realm.tenant_id, group=g, user_id=uuid.uuid4()
        )
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            GroupMembership.objects.create(
                tenant_id=active_realm.tenant_id, group=g, user_id=g.memberships.first().user_id
            )


# ── User profile ─────────────────────────────────────────────────────────


class TestUserProfile:
    def test_record_login_resets_failures(self, active_realm):
        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="alice",
            email="a@x.io",
            failed_login_count=3,
        )
        u.record_login()
        u.refresh_from_db()
        assert u.failed_login_count == 0
        assert u.last_login_at is not None

    def test_record_failed_login_locks_after_threshold(self, active_realm):
        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="bob",
            email="b@x.io",
        )
        for _ in range(5):
            u.record_failed_login(lock_threshold=5)
        u.refresh_from_db()
        assert u.failed_login_count == 5
        assert u.locked_until is not None
        assert u.is_locked is True

    def test_is_locked_false_when_expired(self, active_realm):
        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="c",
            email="c@x.io",
            locked_until=timezone.now() - timezone.timedelta(minutes=1),
        )
        assert u.is_locked is False

    def test_unique_username_per_realm(self, active_realm):
        UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="dup",
            email="a@x.io",
        )
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            UserProfile.objects.create(
                tenant_id=active_realm.tenant_id,
                realm=active_realm,
                keycloak_user_id=uuid.uuid4(),
                username="dup",
                email="b@x.io",
            )


# ── Sessions ─────────────────────────────────────────────────────────────


class TestUserSession:
    def _session(self, active_realm):
        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="u",
            email="u@x.io",
        )
        return UserSession.objects.create(
            tenant_id=active_realm.tenant_id,
            user=u,
            keycloak_session_id=str(uuid.uuid4()),
        )

    def test_revoke(self, active_realm):
        s = self._session(active_realm)
        s.revoke("user_request")
        s.refresh_from_db()
        assert s.status == SessionStatus.REVOKED
        assert s.revoked_at is not None
        assert s.revoked_reason == "user_request"

    def test_touch(self, active_realm):
        s = self._session(active_realm)
        prior = s.last_activity_at
        s.touch()
        s.refresh_from_db()
        assert s.last_activity_at >= prior


# ── Login audit ──────────────────────────────────────────────────────────


class TestLoginAudit:
    def test_create(self, active_realm):
        e = LoginAudit.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            outcome="success",
            username_attempted="u",
            ip_address="10.0.0.1",
        )
        assert e.outcome == "success"
        assert "u" in str(e)


# ── Device + WebAuthn ────────────────────────────────────────────────────


class TestDeviceAndWebAuthn:
    def test_device_active(self, active_realm):
        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="u",
            email="u@x.io",
        )
        d = DeviceRegistration.objects.create(
            tenant_id=active_realm.tenant_id,
            user=u,
            name="iPhone",
            device_type="mobile",
            platform="iOS",
        )
        assert d.is_active is True
        assert "iPhone" in str(d)

    def test_device_revoked(self, active_realm):
        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="u",
            email="u@x.io",
        )
        d = DeviceRegistration.objects.create(
            tenant_id=active_realm.tenant_id,
            user=u,
            name="k",
            device_type="hw_key",
            revoked_at=timezone.now(),
        )
        assert d.is_active is False

    def test_webauthn_unique_credential_id(self, active_realm):
        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="u",
            email="u@x.io",
        )
        WebAuthnCredential.objects.create(
            tenant_id=active_realm.tenant_id,
            user=u,
            credential_id="abc",
            public_key="k",
            label="k1",
        )
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            WebAuthnCredential.objects.create(
                tenant_id=active_realm.tenant_id,
                user=u,
                credential_id="abc",
                public_key="k2",
                label="k2",
            )


# ── Break-glass ──────────────────────────────────────────────────────────


class TestBreakGlass:
    def _user(self, active_realm):
        return UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="doc",
            email="d@x.io",
        )

    def test_lifecycle(self, active_realm):
        user = self._user(active_realm)
        bg = BreakGlassService().request(
            user=user,
            realm=active_realm,
            reason=BreakGlassReason.CLINICAL,
            justification="Mass casualty incident",
            target_resource="patient",
            target_action="override-consent",
        )
        assert bg.status == BreakGlassStatus.REQUESTED
        metrics_before = metrics.break_glass_requested_total

        BreakGlassService().approve(bg, approver="chief1", second_approver="chief2")
        bg.refresh_from_db()
        assert bg.status == BreakGlassStatus.APPROVED
        assert bg.approved_by == "chief1"
        assert bg.second_approver == "chief2"

        BreakGlassService().activate(bg, duration_seconds=600)
        bg.refresh_from_db()
        assert bg.status == BreakGlassStatus.ACTIVE
        assert bg.expires_at is not None
        assert metrics.break_glass_requested_total == metrics_before  # request unchanged

    def test_approve_requires_dual(self, active_realm):
        user = self._user(active_realm)
        bg = BreakGlassService().request(
            user=user,
            realm=active_realm,
            reason=BreakGlassReason.SECURITY,
            justification="Active intrusion",
            target_resource="audit",
            target_action="disable-waf",
        )
        with pytest.raises(ValueError):
            BreakGlassService().approve(bg, approver="only-one", second_approver="")

    def test_activate_requires_approved(self, active_realm):
        user = self._user(active_realm)
        bg = BreakGlassService().request(
            user=user,
            realm=active_realm,
            reason=BreakGlassReason.OPERATIONAL,
            justification="Outage",
            target_resource="db",
            target_action="failover",
        )
        with pytest.raises(ValueError):
            BreakGlassService().activate(bg)

    def test_expire_due(self, active_realm):
        user = self._user(active_realm)
        bg = BreakGlassService().request(
            user=user,
            realm=active_realm,
            reason=BreakGlassReason.COMPLIANCE,
            justification="Legal hold",
            target_resource="ledger",
            target_action="freeze-account",
        )
        BreakGlassService().approve(bg, approver="a", second_approver="b")
        BreakGlassService().activate(bg, duration_seconds=1)
        # Force expire
        bg.expires_at = timezone.now() - timezone.timedelta(seconds=10)
        bg.save()
        count = BreakGlassService().expire_due()
        assert count >= 1
        bg.refresh_from_db()
        assert bg.status == BreakGlassStatus.EXPIRED

    def test_revoke(self, active_realm):
        user = self._user(active_realm)
        bg = BreakGlassService().request(
            user=user,
            realm=active_realm,
            reason=BreakGlassReason.CLINICAL,
            justification="",
            target_resource="x",
            target_action="y",
        )
        bg.revoke()
        bg.refresh_from_db()
        assert bg.status == BreakGlassStatus.REVOKED

    def test_is_expired(self, active_realm):
        user = self._user(active_realm)
        bg = BreakGlassService().request(
            user=user,
            realm=active_realm,
            reason=BreakGlassReason.CLINICAL,
            justification="",
            target_resource="x",
            target_action="y",
        )
        assert bg.is_expired() is False
        bg.expires_at = timezone.now() - timezone.timedelta(seconds=10)
        bg.save()
        assert bg.is_expired() is True


# ── Keycloak admin client (fake mode) ────────────────────────────────────


class TestKeycloakAdminClient:
    def test_authenticate_returns_token(self, fake_kc):
        with patch.object(
            settings := __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            token = fake_kc.authenticate()
        assert token.startswith("fake-admin-token-")

    def test_create_realm_fake(self, fake_kc):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            fake_kc.authenticate()
            r = fake_kc.create_realm({"realm": "alpha", "enabled": True})
        assert r["realm"] == "alpha"
        assert "alpha" in fake_kc._fake_store["realms"]

    def test_delete_realm_fake(self, fake_kc):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            fake_kc.authenticate()
            fake_kc.create_realm({"realm": "alpha", "enabled": True})
            fake_kc.delete_realm("alpha")
        assert "alpha" not in fake_kc._fake_store["realms"]

    def test_client_secret_round_trip(self, fake_kc):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            fake_kc.authenticate()
            fake_kc.create_client("r1", {"clientId": "c1"})
            s = fake_kc.regenerate_client_secret("r1", "c1")
        assert s["type"] == "secret"
        assert s["value"].startswith("fake-secret-")


# ── JWKS cache ───────────────────────────────────────────────────────────


class TestJWKSCache:
    def test_fake_mode_returns_empty_keys(self):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            cache_inst = JWKSCache(jwks_uri="http://x/jwks")
            data = cache_inst.get_keys()
        assert "keys" in data


# ── Token validator ──────────────────────────────────────────────────────


class TestTokenValidator:
    def test_fake_mode_no_jwk_raises(self):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            v = TokenValidator()
        with pytest.raises(TokenValidationError):
            v.validate("not-a-real-token")


# ── Realm service ────────────────────────────────────────────────────────


class TestRealmService:
    def test_provision_creates_realm_and_config(self, active_realm, db):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            svc = RealmService()
            realm = svc.provision(
                tenant_id=uuid.uuid4(),
                realm_name="new-realm",
                realm_type=RealmType.WORKLOAD,
                display_name="New",
                mfa_methods=["webauthn"],
            )
        assert realm.status == RealmStatus.PENDING
        assert hasattr(realm, "configuration")
        assert "webauthn" in realm.configuration.mfa_required_methods

    def test_activate_via_service(self, realm):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            updated = RealmService().activate(realm)
        assert updated.status == RealmStatus.ACTIVE

    def test_decommission_via_service(self, active_realm):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            updated = RealmService().decommission(active_realm)
        assert updated.status == RealmStatus.DECOMMISSIONED


# ── Client service ───────────────────────────────────────────────────────


class TestClientService:
    def test_register_creates_client(self, active_realm):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            c = ClientService().register(
                active_realm,
                client_id="web-app",
                name="Web App",
                redirect_uris=["http://app/cb"],
                public_client=True,
            )
        assert c.client_id == "web-app"
        assert c.public_client is True
        assert c.mfa_required is True

    def test_rotate_secret_replaces_prior(self, active_realm):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            c = ClientService().register(active_realm, client_id="web", name="W")
            row1, txt1 = ClientService().rotate_secret(c, created_by="admin")
            row2, txt2 = ClientService().rotate_secret(c, created_by="admin")
            row1.refresh_from_db()
        assert txt1 != txt2
        assert row1.is_active is False
        assert row2.is_active is True
        assert row2.expires_at is not None


# ── User provisioning service ────────────────────────────────────────────


class TestUserProvisioningService:
    def test_provision_user_creates_profile(self, active_realm):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            u = UserProvisioningService().provision_user(
                active_realm,
                username="doc1",
                email="d1@x.io",
                first_name="Doc",
                last_name="One",
            )
        assert u.username == "doc1"
        assert u.enabled is True
        assert u.display_name == "Doc One"

    def test_provision_user_idempotent(self, active_realm):
        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            u1 = UserProvisioningService().provision_user(
                active_realm, username="x", email="x@x.io"
            )
            u2 = UserProvisioningService().provision_user(
                active_realm, username="x", email="x@x.io"
            )
        assert u1.id == u2.id


# ── Role sync ────────────────────────────────────────────────────────────


class TestRoleSyncService:
    def test_ensure_role_idempotent(self, active_realm):
        r1 = RoleSyncService().ensure_role(active_realm, "admin", display_name="Admin")
        r2 = RoleSyncService().ensure_role(active_realm, "admin", display_name="Admin")
        assert r1.id == r2.id

    def test_attach_permission(self, active_realm):
        r = RoleSyncService().ensure_role(active_realm, "viewer")
        p = RoleSyncService().ensure_permission("platform", "read", "audit")
        ra = RoleSyncService().attach_permission(r, p)
        assert ra.permission_id == p.id


# ── Session service ──────────────────────────────────────────────────────


class TestSessionService:
    def _session(self, active_realm, user=None):
        u = user or UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username=f"u-{uuid.uuid4().hex[:8]}",
            email=f"u-{uuid.uuid4().hex[:8]}@x.io",
        )
        return UserSession.objects.create(
            tenant_id=active_realm.tenant_id,
            user=u,
            keycloak_session_id=str(uuid.uuid4()),
        )

    def test_revoke_all_for_user(self, active_realm):
        user = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="alice-revoke",
            email="alice@x.io",
        )
        s1 = self._session(active_realm, user=user)
        s2 = self._session(active_realm, user=user)
        n = SessionService().revoke_all_for_user(user)
        assert n == 2
        s1.refresh_from_db()
        s2.refresh_from_db()
        assert s1.status == SessionStatus.REVOKED
        assert s2.status == SessionStatus.REVOKED

    def test_enforce_idle_timeout(self, active_realm):
        s = self._session(active_realm)
        s.last_activity_at = timezone.now() - timezone.timedelta(hours=2)
        s.save()
        revoked = SessionService().enforce_idle_timeout()
        assert revoked >= 1
        s.refresh_from_db()
        assert s.status == SessionStatus.IDLE_TIMEOUT


# ── Audit service ────────────────────────────────────────────────────────


class TestAuditService:
    def test_record_login_increments_metrics(self, active_realm):
        from platform.cyidentity.services import AuditService

        before = metrics.login_total
        AuditService.record_login(
            realm=active_realm,
            username_attempted="u",
            outcome="success",
            ip_address="10.0.0.1",
        )
        assert metrics.login_total == before + 1

    def test_record_login_failure(self, active_realm):
        from platform.cyidentity.services import AuditService

        before = metrics.login_failure_total
        AuditService.record_login(
            realm=active_realm,
            username_attempted="u",
            outcome="failure",
            failure_reason="bad_password",
        )
        assert metrics.login_failure_total == before + 1

    def test_record_emits_to_platform_sink(self, active_realm):
        from platform.audit.models import AuditLog
        from platform.cyidentity.services import AuditService

        AuditService.record(
            action="create",
            resource_type="realm",
            resource_id=str(active_realm.id),
            tenant_id=active_realm.tenant_id,
        )
        assert AuditLog.objects.filter(resource_type="realm").exists()


# ── Metrics renderer ─────────────────────────────────────────────────────


class TestMetricsRenderer:
    def test_render_prometheus(self):
        out = render_prometheus()
        assert "cybercom_identity_login_total" in out
        assert "TYPE" in out


# ── API endpoints ────────────────────────────────────────────────────────


class TestIdentityHealthAPI:
    def test_health_endpoint(self, admin_client, active_realm):
        resp = admin_client.get("/api/v1/identity/healthz/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["realm_count"] >= 1
        assert body["active_realm_count"] >= 1

    def test_metrics_endpoint(self, admin_client):
        resp = admin_client.get("/api/v1/identity/metrics")
        assert resp.status_code == 200
        assert b"cybercom_identity_login_total" in resp.content


class TestTokenValidateAPI:
    def test_invalid_token(self, admin_client):
        resp = admin_client.post(
            "/api/v1/identity/token/validate/", {"token": "garbage"}, format="json"
        )
        assert resp.status_code == 401
        assert resp.json()["valid"] is False


# ── Celery tasks ─────────────────────────────────────────────────────────


class TestCyIdentityTasks:
    def test_expire_break_glass_task(self, active_realm):
        from platform.cyidentity.tasks import expire_break_glass_task

        user = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="u",
            email="u@x.io",
        )
        bg = BreakGlassService().request(
            user=user,
            realm=active_realm,
            reason=BreakGlassReason.CLINICAL,
            justification="x" * 20,
            target_resource="x",
            target_action="y",
        )
        BreakGlassService().approve(bg, approver="a", second_approver="b")
        BreakGlassService().activate(bg, duration_seconds=1)
        bg.expires_at = timezone.now() - timezone.timedelta(seconds=10)
        bg.save()
        assert expire_break_glass_task() >= 1

    def test_enforce_idle_timeout_task(self, active_realm):
        from platform.cyidentity.tasks import enforce_idle_timeout_task

        u = UserProfile.objects.create(
            tenant_id=active_realm.tenant_id,
            realm=active_realm,
            keycloak_user_id=uuid.uuid4(),
            username="u",
            email="u@x.io",
        )
        s = UserSession.objects.create(
            tenant_id=active_realm.tenant_id,
            user=u,
            keycloak_session_id=str(uuid.uuid4()),
            last_activity_at=timezone.now() - timezone.timedelta(hours=2),
        )
        revoked = enforce_idle_timeout_task()
        assert revoked >= 1
        s.refresh_from_db()
        assert s.status == SessionStatus.IDLE_TIMEOUT

    def test_rotate_client_secret_task(self, active_realm):
        from platform.cyidentity.tasks import rotate_client_secret_task

        with patch.object(
            __import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True
        ):
            ClientService().register(active_realm, client_id="rotate", name="R")
            result = rotate_client_secret_task("rotate", created_by="admin")
        assert result["client_id"] == "rotate"
        assert result["secret_hint"]


# ── Signals ──────────────────────────────────────────────────────────────


class TestSignals:
    def test_realm_status_change_emits_audit(self, active_realm):
        from platform.audit.models import AuditLog

        active_realm.status = RealmStatus.SUSPENDED
        active_realm.save()
        assert AuditLog.objects.filter(resource_type="realm", action="update").exists()

    def test_client_secret_create_emits_audit(self, active_realm):
        from platform.audit.models import AuditLog

        c = ApplicationClient.objects.create(realm=active_realm, client_id="cs", name="cs")
        ClientSecret.objects.create(
            tenant_id=active_realm.tenant_id,
            client=c,
            secret_hash="h",
            secret_hint="abcd",
        )
        assert AuditLog.objects.filter(resource_type="client_secret", action="create").exists()


# ── Permissions ──────────────────────────────────────────────────────────


class TestPermissions:
    def test_is_platform_admin_no_claims(self, rf):
        from platform.cyidentity.permissions import IsPlatformAdmin

        request = rf.get("/")
        request.auth_claims = {}
        assert IsPlatformAdmin().has_permission(request, None) is False

    def test_is_platform_admin_with_role(self, rf):
        from platform.cyidentity.permissions import IsPlatformAdmin

        request = rf.get("/")
        request.auth_claims = {"realm_access": {"roles": ["platform_admin"]}}
        assert IsPlatformAdmin().has_permission(request, None) is True

    def test_readonly_or_admin_get_allowed(self, rf):
        from platform.cyidentity.permissions import ReadOnlyOrPlatformAdmin

        request = rf.get("/")
        request.auth_claims = {}
        assert ReadOnlyOrPlatformAdmin().has_permission(request, None) is True

    def test_readonly_or_admin_post_denied(self, rf):
        from platform.cyidentity.permissions import ReadOnlyOrPlatformAdmin

        request = rf.post("/")
        request.auth_claims = {}
        assert ReadOnlyOrPlatformAdmin().has_permission(request, None) is False

    def test_tenant_scoped_match(self, rf):
        from platform.cyidentity.permissions import IsTenantScoped

        request = rf.get("/")
        tid = uuid.uuid4()
        request.auth_claims = {"tenant_id": str(tid)}
        obj = type("O", (), {"tenant_id": tid})()
        assert IsTenantScoped().has_object_permission(request, None, obj) is True

    def test_tenant_scoped_mismatch(self, rf):
        from platform.cyidentity.permissions import IsTenantScoped

        request = rf.get("/")
        request.auth_claims = {"tenant_id": str(uuid.uuid4())}
        obj = type("O", (), {"tenant_id": uuid.uuid4()})()
        assert IsTenantScoped().has_object_permission(request, None, obj) is False

    def test_break_glass_dual_approval_required(self, rf):
        from platform.cyidentity.permissions import BreakGlassRequiresDualApproval

        view = type("V", (), {"action": "approve"})()
        request = rf.post("/", data={"approver": "a"}, format="json")
        request.data = {"approver": "a"}  # no second_approver
        assert BreakGlassRequiresDualApproval().has_permission(request, view) is False

        request.data = {"approver": "a", "second_approver": "b"}
        assert BreakGlassRequiresDualApproval().has_permission(request, view) is True


# ── Identity metrics snapshot ────────────────────────────────────────────


class TestIdentityMetrics:
    def test_snapshot(self):
        m = IdentityMetrics()
        m.login_total = 7
        m.login_latency_ms = [10, 20, 30, 40, 50]
        snap = m.snapshot()
        assert snap["login_total"] == 7
        assert snap["login_latency_ms_p50"] == 30
        assert snap["login_latency_ms_p95"] == 50
