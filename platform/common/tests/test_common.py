import uuid
import pytest
from rest_framework.test import APIClient
import jwt

from platform.common.security.vault import VaultClient
from platform.common.security.opa import OPAPolicyEngine

@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()

@pytest.fixture
def auth_client(test_tenant_id):
    client = APIClient()
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "admin@cybercom.io",
        "tenant_id": str(test_tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(test_tenant_id),
    )
    return client

class TestVaultClient:
    def test_default_secrets(self):
        db_secrets = VaultClient.get_secret("cybercom/database")
        assert db_secrets["username"] == "postgres"
        
        kc_secrets = VaultClient.get_secret("cybercom/keycloak")
        assert kc_secrets["client_secret"] == "fake-vault-keycloak-secret"

        custom_secrets = VaultClient.get_secret("cybercom/random")
        assert custom_secrets["value"] == "mock-secret-value"

    def test_write_and_read(self):
        path = "cybercom/custom/path"
        data = {"key1": "val1", "key2": "val2"}
        VaultClient.write_secret(path, data)
        assert VaultClient.get_secret(path) == data


class TestOPAPolicyEngine:
    def test_admin_policy(self):
        assert OPAPolicyEngine.evaluate_policy("platform/admin", {"roles": ["platform_admin"]}) is True
        assert OPAPolicyEngine.evaluate_policy("platform/admin", {"roles": ["clinician"]}) is False

    def test_clinical_access_policy(self):
        # Clinician role
        assert OPAPolicyEngine.evaluate_policy(
            "clinical/access",
            {"action": "write", "roles": ["clinician"]}
        ) is True

        # Break glass active
        assert OPAPolicyEngine.evaluate_policy(
            "clinical/access",
            {"action": "write", "roles": ["other"], "break_glass_active": True}
        ) is True

        # Read/view action by patient_viewer
        assert OPAPolicyEngine.evaluate_policy(
            "clinical/access",
            {"action": "read", "roles": ["patient_viewer"]}
        ) is True

        # Reject mutation by patient_viewer
        assert OPAPolicyEngine.evaluate_policy(
            "clinical/access",
            {"action": "write", "roles": ["patient_viewer"]}
        ) is False

        # Reject all other cases
        assert OPAPolicyEngine.evaluate_policy(
            "clinical/access",
            {"action": "write", "roles": ["unprivileged"]}
        ) is False

    def test_default_policy(self):
        assert OPAPolicyEngine.evaluate_policy("some/other/policy", {"roles": ["user"]}) is True
        assert OPAPolicyEngine.evaluate_policy("some/other/policy", {"roles": []}) is False


@pytest.mark.django_db
class TestCommonAPIs:
    def test_platform_metrics_unauthenticated(self):
        client = APIClient()
        resp = client.get("/api/v1/common/dashboard-metrics/")
        assert resp.status_code == 401

    def test_platform_metrics(self, auth_client):
        resp = auth_client.get("/api/v1/common/dashboard-metrics/")
        assert resp.status_code == 200
        assert "security_compliance" in resp.data
        assert resp.data["platform_hardening"]["vault_secret_store"] == "healthy"
        assert resp.data["platform_hardening"]["opa_runtime_engine"] == "healthy"
