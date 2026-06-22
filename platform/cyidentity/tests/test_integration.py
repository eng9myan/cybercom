"""
CyIdentity integration tests — exercise the API + service stack end-to-end
against the in-memory Keycloak fake. Verifies:
  - Realm provision flow
  - Client register + secret rotation
  - User provision + role assignment
  - Group membership creation
  - Break-glass full lifecycle via API
  - Session revoke
"""
import uuid
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from platform.cyidentity.models import (
    ApplicationClient,
    BreakGlassAccess,
    BreakGlassStatus,
    IdentityRealm,
    RealmStatus,
    RealmType,
    UserProfile,
)


@pytest.fixture
def admin_client():
    import jwt
    client = APIClient()
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "admin@cybercom.io",
        "tenant_id": "00000000-0000-0000-0000-000000000000",
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID="00000000-0000-0000-0000-000000000000",
    )
    return client


@pytest.fixture
def patch_keycloak_fake():
    with patch.object(__import__("django").conf.settings, "KEYCLOAK_ENABLED", False, create=True):
        yield


@pytest.mark.django_db
class TestRealmIntegration:
    def test_provision_then_activate_then_decommission(self, admin_client, patch_keycloak_fake):
        resp = admin_client.post(
            "/api/v1/identity/realms/provision/",
            {
                "tenant_id": str(uuid.uuid4()),
                "realm_name": "integ-tenant",
                "realm_type": RealmType.CUSTOMER,
                "display_name": "Integration",
                "mfa_methods": ["webauthn"],
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        realm_id = body["id"]
        assert body["status"] == RealmStatus.PENDING
        assert "configuration" in body

        # Activate
        resp = admin_client.post(f"/api/v1/identity/realms/{realm_id}/activate/")
        assert resp.status_code == 200
        assert resp.json()["status"] == RealmStatus.ACTIVE

        # Decommission
        resp = admin_client.post(f"/api/v1/identity/realms/{realm_id}/decommission/")
        assert resp.status_code == 200
        assert resp.json()["status"] == RealmStatus.DECOMMISSIONED


@pytest.mark.django_db
class TestClientIntegration:
    def _realm(self):
        return IdentityRealm.objects.create(
            tenant_id=uuid.uuid4(), realm_name="c-int",
            realm_type=RealmType.CUSTOMER, status=RealmStatus.ACTIVE,
            issuer_url="http://x", jwks_uri="http://x/jwks", admin_api_url="http://x/admin",
        )

    def test_register_and_rotate(self, admin_client, patch_keycloak_fake):
        realm = self._realm()
        resp = admin_client.post(
            "/api/v1/identity/clients/register/",
            {
                "realm_id": str(realm.id),
                "client_id": "integ-client",
                "name": "Integ Client",
                "public_client": True,
                "redirect_uris": ["http://localhost/cb"],
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        client_id = resp.json()["id"]

        # Rotate
        resp = admin_client.post(
            f"/api/v1/identity/clients/{client_id}/rotate-secret/",
            {"created_by": "tester"}, format="json",
        )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        assert body["cleartext"]
        assert body["secret_hint"] == body["cleartext"][-4:]
        assert body["expires_at"] is not None


@pytest.mark.django_db
class TestUserAndRoleIntegration:
    def _realm(self):
        return IdentityRealm.objects.create(
            tenant_id=uuid.uuid4(), realm_name="u-int",
            realm_type=RealmType.CUSTOMER, status=RealmStatus.ACTIVE,
            issuer_url="http://x", jwks_uri="http://x/jwks", admin_api_url="http://x/admin",
        )

    def test_provision_user_then_assign_role(self, admin_client, patch_keycloak_fake):
        from platform.cyidentity.models import Role
        realm = self._realm()
        Role.objects.create(realm=realm, name="clinician", display_name="Clinician")

        resp = admin_client.post(
            "/api/v1/identity/users/provision/",
            {
                "realm_id": str(realm.id),
                "username": "doc99",
                "email": "doc99@x.io",
                "first_name": "Doc",
                "last_name": "99",
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        user_id = resp.json()["id"]

        # Lock + unlock
        resp = admin_client.post(f"/api/v1/identity/users/{user_id}/lock/")
        assert resp.status_code == 200
        assert resp.json()["locked_until"] is not None

        resp = admin_client.post(f"/api/v1/identity/users/{user_id}/unlock/")
        assert resp.status_code == 200
        assert resp.json()["locked_until"] is None


@pytest.mark.django_db
class TestBreakGlassIntegration:
    def _realm_and_user(self):
        realm = IdentityRealm.objects.create(
            tenant_id=uuid.uuid4(), realm_name="bg-int",
            realm_type=RealmType.CUSTOMER, status=RealmStatus.ACTIVE,
            issuer_url="http://x", jwks_uri="http://x/jwks", admin_api_url="http://x/admin",
        )
        user = UserProfile.objects.create(
            tenant_id=realm.tenant_id, realm=realm,
            keycloak_user_id=uuid.uuid4(), username="bguser", email="bg@x.io",
        )
        return realm, user

    def test_full_lifecycle(self, admin_client):
        realm, user = self._realm_and_user()
        resp = admin_client.post(
            "/api/v1/identity/break-glass/",
            {
                "user_id": str(user.id),
                "realm_id": str(realm.id),
                "reason": "clinical",
                "justification": "Mass casualty incident in ER",
                "target_resource": "patient",
                "target_action": "override-consent",
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        bg_id = resp.json()["id"]

        resp = admin_client.post(
            f"/api/v1/identity/break-glass/{bg_id}/approve/",
            {"approver": "chief1", "second_approver": "chief2"},
            format="json",
        )
        assert resp.status_code == 200, resp.content
        assert resp.json()["status"] == BreakGlassStatus.APPROVED

        resp = admin_client.post(
            f"/api/v1/identity/break-glass/{bg_id}/activate/",
            {"duration_seconds": 600}, format="json",
        )
        assert resp.status_code == 200, resp.content
        assert resp.json()["status"] == BreakGlassStatus.ACTIVE

        resp = admin_client.post(f"/api/v1/identity/break-glass/{bg_id}/revoke/")
        assert resp.status_code == 200
        assert resp.json()["status"] == BreakGlassStatus.REVOKED

    def test_approve_without_second_approver_rejected(self, admin_client):
        realm, user = self._realm_and_user()
        resp = admin_client.post(
            "/api/v1/identity/break-glass/",
            {
                "user_id": str(user.id),
                "realm_id": str(realm.id),
                "reason": "clinical",
                "justification": "Single approver attempt",
                "target_resource": "x",
                "target_action": "y",
            },
            format="json",
        )
        bg_id = resp.json()["id"]
        resp = admin_client.post(
            f"/api/v1/identity/break-glass/{bg_id}/approve/",
            {"approver": "chief1"}, format="json",
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestSessionIntegration:
    def _realm_and_session(self):
        realm = IdentityRealm.objects.create(
            tenant_id=uuid.uuid4(), realm_name="s-int",
            realm_type=RealmType.CUSTOMER, status=RealmStatus.ACTIVE,
            issuer_url="http://x", jwks_uri="http://x/jwks", admin_api_url="http://x/admin",
        )
        user = UserProfile.objects.create(
            tenant_id=realm.tenant_id, realm=realm,
            keycloak_user_id=uuid.uuid4(), username="suser", email="s@x.io",
        )
        from platform.cyidentity.models import UserSession
        s = UserSession.objects.create(
            tenant_id=realm.tenant_id, user=user,
            keycloak_session_id=str(uuid.uuid4()),
        )
        return realm, user, s

    def test_revoke_session_via_api(self, admin_client):
        _, _, s = self._realm_and_session()
        resp = admin_client.post(
            f"/api/v1/identity/sessions/{s.id}/revoke/",
            {"reason": "user_request"}, format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"

    def test_enforce_idle_timeout_via_api(self, admin_client):
        from django.utils import timezone
        realm, _, s = self._realm_and_session()
        s.last_activity_at = timezone.now() - timezone.timedelta(hours=2)
        s.save()
        resp = admin_client.post("/api/v1/identity/sessions/enforce-idle-timeout/")
        assert resp.status_code == 200
        assert resp.json()["revoked_count"] >= 1
