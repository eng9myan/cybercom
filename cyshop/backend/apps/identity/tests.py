import time
import uuid
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant
from apps.identity.models import Role, RoleAssignment
import json

User = get_user_model()

class IdentityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Gamma Ltd", subdomain="gamma")
        self.register_url = "/api/v1/identity/register/"
        self.login_url = "/api/v1/identity/login/"
        
        self.user_data = {
            "username": "testuser",
            "email": "test@gamma.com",
            "password": "securepassword123",
            "tenant_id": str(self.tenant.id)
        }

    def test_user_registration_and_login(self):
        # 1. Register User
        reg_response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type="application/json"
        )
        self.assertEqual(reg_response.status_code, 201)
        
        # Verify user created in DB
        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@gamma.com")
        self.assertEqual(user.tenant_id, self.tenant.id)

        # 2. Login User
        login_data = {
            "username": "testuser",
            "password": "securepassword123"
        }
        login_response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type="application/json"
        )
        self.assertEqual(login_response.status_code, 200)
        data = login_response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["username"], "testuser")

    def test_role_assignment(self):
        # Create user
        user = User.objects.create_user(
            username="adminuser", 
            email="admin@gamma.com", 
            password="adminpassword",
            tenant_id=self.tenant.id
        )
        role = Role.objects.create(code="ADMIN", name="Administrator", tenant_id=self.tenant.id)
        assignment = RoleAssignment.objects.create(
            tenant_id=self.tenant.id,
            user=user,
            role=role
        )
        
        self.assertEqual(assignment.user, user)
        self.assertEqual(assignment.role.code, "ADMIN")
        self.assertEqual(user.role_assignments.first().role.code, "ADMIN")


class CyIDExchangeTestCase(TestCase):
    """CyID ecosystem, Phase 3 — real RS256 token verification against a
    mocked JWKS endpoint (same person, same credential, reaching cyshop
    instead of a Keycloak-backed product), mirroring the mint_token/
    mock_jwks pattern used for cymed/cycom's real auth-path tests."""

    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Delta Retail", subdomain="delta")
        self.exchange_url = "/api/v1/identity/cyid-exchange/"

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self.public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def _mint(self, payload):
        claims = {**payload}
        now = int(time.time())
        claims.setdefault("iat", now)
        claims.setdefault("exp", now + 3600)
        return jwt.encode(claims, self.private_pem, algorithm="RS256")

    def _mock_jwks(self):
        fake_signing_key = type("FakeSigningKey", (), {"key": self.public_pem})()
        fake_client = type(
            "FakeJWKClient", (), {"get_signing_key_from_jwt": lambda self, token: fake_signing_key}
        )()
        return patch("apps.identity.cyid_bridge._get_jwks_client", return_value=fake_client)

    def test_exchange_jit_provisions_user_and_mints_cyshop_session(self):
        person_id = str(uuid.uuid4())
        token = self._mint({"sub": person_id, "person_id": person_id, "email": "jane@example.com"})

        with self._mock_jwks():
            resp = self.client.post(
                self.exchange_url,
                data=json.dumps({"cyid_token": token, "tenant_id": str(self.tenant.id)}),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertIn("access_token", body)
        self.assertEqual(body["tenant_id"], str(self.tenant.id))

        user = User.objects.get(cyid_person_id=person_id)
        self.assertEqual(str(user.tenant_id), str(self.tenant.id))
        self.assertEqual(user.email, "jane@example.com")

    def test_second_exchange_reuses_same_user_not_a_duplicate(self):
        person_id = str(uuid.uuid4())
        token = self._mint({"sub": person_id, "person_id": person_id, "email": "sam@example.com"})

        with self._mock_jwks():
            self.client.post(
                self.exchange_url,
                data=json.dumps({"cyid_token": token, "tenant_id": str(self.tenant.id)}),
                content_type="application/json",
            )
            resp2 = self.client.post(
                self.exchange_url,
                data=json.dumps({"cyid_token": token, "tenant_id": str(self.tenant.id)}),
                content_type="application/json",
            )
        self.assertEqual(resp2.status_code, 200, resp2.content)
        self.assertEqual(User.objects.filter(cyid_person_id=person_id).count(), 1)

    def test_invalid_token_rejected(self):
        resp = self.client.post(
            self.exchange_url,
            data=json.dumps({"cyid_token": "not-a-real-jwt", "tenant_id": str(self.tenant.id)}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)
