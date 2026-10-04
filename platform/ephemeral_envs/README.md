# platform.ephemeral_envs

Phase 4 (Odoo.sh-equivalent hosting), item 2: per-branch/per-tenant
ephemeral environment provisioning. The missing automation half of
`platform.tenant.TenantEnvironment` (which only *registers* where a real
customer's environment lives — nothing in this repo provisioned anything
before this app).

## What it is

- `EphemeralEnvironment` — tracks one throwaway environment: which app
  (cymed/cycom), which git ref, status, the OCI instance's public IP.
- `services.py` — shells out to Terraform (`infrastructure/terraform/
  ephemeral-env/`) to actually provision/destroy. Fails honestly
  (`TerraformNotConfigured`) without a real `terraform` binary and the
  account-specific OCI variables — never fakes success.
- `tasks.py` — two Celery tasks (`provision`, `destroy`) run the above
  asynchronously so the API returns immediately.
- `views.py` — `POST /api/v1/ephemeral-envs/` (platform_admin only)
  creates the row and enqueues provisioning; `GET` polls status;
  `POST .../<id>/destroy_environment/` tears it down.

## Required configuration (none of this has sensible defaults)

On whatever machine runs the Celery worker that processes these jobs:

```
TERRAFORM_BINARY=/usr/local/bin/terraform   # optional, defaults to `terraform` on PATH
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxxx
OCI_AVAILABILITY_DOMAIN=abCD:AP-SINGAPORE-1-AD-1
OCI_SUBNET_ID=ocid1.subnet.oc1..xxxx
OCI_IMAGE_ID=ocid1.image.oc1..xxxx
OCI_SSH_PUBLIC_KEY="ssh-ed25519 AAAA..."
TERRAFORM_WORKSPACES_DIR=/var/lib/cybercom/ephemeral-envs   # optional
```

Without these, every provision/destroy request still gets accepted and
tracked — it just lands in `status=failed` with a clear
`error_message`, same posture as HyperPay/JoFotara/the e-invoicing
national formats whenever their own credentials aren't configured.

## What's NOT built (flagged, not silently skipped)

- No DNS/TLS/preview-URL routing for ephemeral instances (raw IP:8000 only).
- No automatic teardown on PR-close or an idle timeout — these accumulate
  real cost until someone calls the destroy action.
- No UI — API only. A real "Preview Environments" admin page would
  consume `GET /api/v1/ephemeral-envs/`.
- Not exercised against a real OCI account — the Terraform module and
  this app's own tests are real and pass, but the actual `terraform
  apply` path has only been reviewed, not run against live infrastructure.
