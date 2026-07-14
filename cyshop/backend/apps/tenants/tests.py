from django.test import TestCase, Client
from django.urls import reverse
from apps.tenants.models import Tenant, Company, Branch
import json

class TenantTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Register a primary tenant with all required admin initialization fields
        self.tenant_data = {
            "name": "Acme Corp",
            "subdomain": "acme",
            "email": "admin@acme.com",
            "username": "acmeadmin",
            "password": "securepassword"
        }
        self.register_url = "/api/v1/tenants/register/"
        
    def test_tenant_registration(self):
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.tenant_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("tenant_id", data)
        self.assertIn("company_id", data)
        self.assertIn("branch_id", data)

    def test_middleware_rejects_missing_tenant(self):
        # Accessing an authenticated route (e.g. companies) without tenant context
        # should fail with 400 or login validation checks
        response = self.client.get("/api/v1/tenants/companies/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Missing or invalid X-Tenant-ID header context"})

    def test_middleware_resolves_tenant_header(self):
        tenant = Tenant.objects.create(name="Beta LLC", subdomain="beta")
        # Direct URL lookup should pass the tenant validation check
        response = self.client.get(
            "/api/v1/tenants/companies/",
            HTTP_X_TENANT_ID=str(tenant.id)
        )
        # It fails with 403 Forbidden instead of 400 because tenant check passes but auth is required
        self.assertEqual(response.status_code, 403)
