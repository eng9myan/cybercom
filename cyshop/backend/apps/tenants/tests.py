from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.tenants.models import Tenant, Company, Branch, MarketplaceStatus
import json
import uuid

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


class CyMartEligibilityTestCase(TestCase):
    """
    CyberCom master spec critical test case 3: "A CyShop merchant without a
    signed marketplace agreement cannot sell on CyMart."
    """

    def setUp(self):
        self.tenant_id = uuid.uuid4()

    def _company(self, **overrides):
        defaults = dict(tenant_id=self.tenant_id, name="Test Merchant")
        defaults.update(overrides)
        return Company.objects.create(**defaults)

    def _branch(self, company, **overrides):
        defaults = dict(
            tenant_id=self.tenant_id,
            company=company,
            name="Main Branch",
            address="123 Test St",
        )
        defaults.update(overrides)
        return Branch(**defaults)

    def test_branch_cannot_publish_without_signed_agreement(self):
        company = self._company()
        branch = self._branch(company, marketplace_enabled=True)
        with self.assertRaises(ValidationError):
            branch.save()

    def test_branch_cannot_publish_when_status_not_active(self):
        company = self._company()
        company.sign_marketplace_agreement()  # status -> application_pending, not active
        branch = self._branch(company, marketplace_enabled=True)
        with self.assertRaises(ValidationError):
            branch.save()

    def test_branch_cannot_publish_without_customer_facing_store(self):
        company = self._company(operates_customer_facing_store=False)
        company.sign_marketplace_agreement()
        company.marketplace_status = MarketplaceStatus.ACTIVE
        company.save()
        branch = self._branch(company, marketplace_enabled=True)
        with self.assertRaises(ValidationError):
            branch.save()

    def test_branch_can_publish_once_fully_eligible(self):
        company = self._company()
        company.sign_marketplace_agreement()
        company.marketplace_status = MarketplaceStatus.ACTIVE
        company.save()
        branch = self._branch(company, marketplace_enabled=True)
        branch.save()  # should not raise
        self.assertTrue(Branch.objects.get(pk=branch.pk).marketplace_enabled)

    def test_branch_not_marketplace_enabled_can_save_regardless(self):
        # A non-published branch must never be blocked by eligibility rules.
        company = self._company()
        branch = self._branch(company, marketplace_enabled=False)
        branch.save()
        self.assertFalse(Branch.objects.get(pk=branch.pk).marketplace_enabled)
