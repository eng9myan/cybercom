from django.test import TestCase, Client
from apps.tenants.models import Tenant
from apps.audit.models import SystemAuditLog
import json

class AuditTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Delta Inc", subdomain="delta")
        
    def test_audit_logs_on_post_tenant_registration(self):
        # Initial logs count should be 0
        self.assertEqual(SystemAuditLog.objects.count(), 0)
        
        # Make a POST request that triggers database modifications
        # Under tenants/register/, which is excluded from tenant header checks
        tenant_data = {
            "name": "Audit Test Tenant",
            "subdomain": "audittest",
            "email": "auditadmin@audittest.com",
            "username": "auditadmin",
            "password": "securepassword123"
        }
        response = self.client.post(
            "/api/v1/tenants/register/",
            data=json.dumps(tenant_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        
        # Verify an audit log entry was created
        self.assertEqual(SystemAuditLog.objects.count(), 1)
        log = SystemAuditLog.objects.first()
        self.assertEqual(log.method, "POST")
        self.assertEqual(log.path, "/api/v1/tenants/register/")
        self.assertIn("API Request: POST", log.action)
