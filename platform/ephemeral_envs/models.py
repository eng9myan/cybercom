from django.db import models

from platform.common.models import PlatformModel


class EphemeralEnvironment(PlatformModel):
    """A throwaway per-branch/per-trial-tenant deployment (Phase 4 hosting,
    item 2) — one OCI instance running a single app at a given git ref,
    provisioned via infrastructure/terraform/ephemeral-env/ and torn down
    the same way. Platform-level, not tenant-scoped: this tracks ops
    infrastructure, not a product tenant's own data.

    Distinct from `platform.tenant.TenantEnvironment` (a per-tenant prod/
    staging/dev topology *registry* — it records where a real customer's
    environment lives, it doesn't provision anything). This model is the
    other half memory flagged as missing ("nothing automates it"): the
    actual IaC-backed provisioning/teardown. `tenant` is optional because
    the primary use case is per-*branch* CI previews with no real customer
    behind them at all; when an environment genuinely is a dedicated copy
    for one customer, set it and consider also writing a TenantEnvironment
    row from the same workflow (not done automatically here)."""

    APPS = [("cymed", "CyMed"), ("cycom", "CyCom")]
    STATUS = [
        ("queued", "Queued"),
        ("provisioning", "Provisioning"),
        ("ready", "Ready"),
        ("failed", "Failed"),
        ("destroying", "Destroying"),
        ("destroyed", "Destroyed"),
        ("destroy_failed", "Destroy Failed"),
    ]

    name = models.SlugField(max_length=41, unique=True, help_text="Branch or tenant slug, e.g. 'pr-482'.")
    tenant = models.ForeignKey(
        "platform_tenant.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="ephemeral_environments",
        help_text="Set only when this environment is a dedicated copy for one real customer, not a CI preview.",
    )
    app = models.CharField(max_length=10, choices=APPS)
    git_ref = models.CharField(max_length=255, default="develop")
    status = models.CharField(max_length=20, choices=STATUS, default="queued", db_index=True)
    public_ip = models.GenericIPAddressField(null=True, blank=True)
    terraform_instance_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    requested_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "platform_ephemeral_environments"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.app}:{self.name} ({self.status})"
