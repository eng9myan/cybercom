import pytest
from rest_framework.test import APIClient

from platform.ephemeral_envs.models import EphemeralEnvironment
from platform.ephemeral_envs import services


def _authed_client(mint_token, mock_jwks, *, roles, tenant_id=None, email="ops@cybercom.io"):
    token = mint_token({
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": email,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "realm_access": {"roles": roles},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestEphemeralEnvironmentApi:
    def test_non_platform_admin_is_refused(self, mint_token, mock_jwks):
        # TenantIsolationMiddleware itself 400s a non-platform_admin role with
        # no tenant_id (a real, separate guard) -- give this one a tenant_id
        # so the request actually reaches IsPlatformAdmin, the thing under test.
        import uuid

        client = _authed_client(mint_token, mock_jwks, roles=["tenant_admin"], tenant_id=uuid.uuid4())
        resp = client.post("/api/v1/ephemeral-envs/", {"name": "pr-1", "app": "cycom"}, format="json")
        assert resp.status_code == 403

    def test_create_enqueues_provisioning_and_fails_honestly_without_terraform(
        self, mint_token, mock_jwks, monkeypatch
    ):
        # No real terraform binary / OCI env vars in this test environment --
        # the task should land the row in "failed" with a clear message,
        # never a fake "ready". This exercises the REAL fail-closed path,
        # not a mock.
        monkeypatch.delenv("OCI_COMPARTMENT_ID", raising=False)
        client = _authed_client(mint_token, mock_jwks, roles=["platform_admin"])
        resp = client.post("/api/v1/ephemeral-envs/", {"name": "pr-482", "app": "cycom"}, format="json")
        assert resp.status_code == 201

        env = EphemeralEnvironment.objects.get(name="pr-482")
        assert env.status == "failed"
        assert "terraform" in env.error_message.lower() or "OCI" in env.error_message

    def test_create_provisions_successfully_when_the_runner_is_mocked(
        self, mint_token, mock_jwks, monkeypatch
    ):
        monkeypatch.setattr(
            services, "provision",
            lambda *, name, app, git_ref, timeout=1800: {"public_ip": "10.0.0.5", "instance_id": "ocid1.instance.fake"},
        )
        client = _authed_client(mint_token, mock_jwks, roles=["platform_admin"])
        resp = client.post(
            "/api/v1/ephemeral-envs/", {"name": "pr-483", "app": "cymed", "git_ref": "feature/x"}, format="json"
        )
        assert resp.status_code == 201

        env = EphemeralEnvironment.objects.get(name="pr-483")
        assert env.status == "ready"
        assert env.public_ip == "10.0.0.5"
        assert env.terraform_instance_id == "ocid1.instance.fake"

    def test_destroy_action_fails_honestly_without_prior_state(self, mint_token, mock_jwks, monkeypatch):
        monkeypatch.delenv("OCI_COMPARTMENT_ID", raising=False)
        env = EphemeralEnvironment.objects.create(name="pr-999", app="cycom", status="ready")
        client = _authed_client(mint_token, mock_jwks, roles=["platform_admin"])
        resp = client.post(f"/api/v1/ephemeral-envs/{env.id}/destroy_environment/")
        assert resp.status_code == 200

        env.refresh_from_db()
        assert env.status == "destroy_failed"
        assert env.error_message

    def test_name_must_be_unique(self, mint_token, mock_jwks):
        EphemeralEnvironment.objects.create(name="dup", app="cycom")
        client = _authed_client(mint_token, mock_jwks, roles=["platform_admin"])
        resp = client.post("/api/v1/ephemeral-envs/", {"name": "dup", "app": "cycom"}, format="json")
        assert resp.status_code == 400


class TestTerraformServiceGuards:
    def test_provision_refuses_without_terraform_binary(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: None)
        with pytest.raises(services.TerraformNotConfigured):
            services.provision(name="x", app="cycom", git_ref="develop")

    def test_destroy_refuses_without_prior_workspace(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TERRAFORM_WORKSPACES_DIR", str(tmp_path))
        monkeypatch.setenv("OCI_COMPARTMENT_ID", "ocid1.compartment.fake")
        monkeypatch.setenv("OCI_AVAILABILITY_DOMAIN", "fake-ad")
        monkeypatch.setenv("OCI_SUBNET_ID", "ocid1.subnet.fake")
        monkeypatch.setenv("OCI_IMAGE_ID", "ocid1.image.fake")
        monkeypatch.setenv("OCI_SSH_PUBLIC_KEY", "ssh-ed25519 AAAA fake")
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/true")
        with pytest.raises(services.TerraformRunError):
            services.destroy(name="never-provisioned")
