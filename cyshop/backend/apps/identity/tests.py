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
