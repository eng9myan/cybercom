# Ephemeral environment (Terraform)

Phase 4 (Odoo.sh-equivalent hosting), item 2. Provisions one throwaway OCI
compute instance running a single app (`cymed` or `cycom`) checked out at a
given git ref — a per-branch or per-trial-tenant environment, fully
isolated from production (own VM, own containers, own generated secrets).

Driven programmatically by `platform.ephemeral_envs`' API/Celery task (see
that app), or run directly:

```bash
cd infrastructure/terraform/ephemeral-env
terraform init
terraform apply \
  -var="compartment_id=ocid1.compartment.oc1..xxxx" \
  -var="availability_domain=abCD:AP-SINGAPORE-1-AD-1" \
  -var="subnet_id=ocid1.subnet.oc1..xxxx" \
  -var="image_id=ocid1.image.oc1..xxxx" \
  -var="ssh_public_key=$(cat ~/.ssh/id_ed25519.pub)" \
  -var="environment_name=pr-482" \
  -var="app=cycom" \
  -var="git_ref=feature/my-branch"
```

`compartment_id`/`availability_domain`/`subnet_id`/`image_id` are account-
and region-specific — there's no sensible default, get them from
`oci iam compartment list` / `oci iam availability-domain list` /
your existing VCN's subnet / `oci compute image list` (an Ubuntu 22.04+
platform image matching the chosen shape's architecture).

First boot takes several minutes (package install, Docker image build,
migrate, realm bootstrap) — poll `output.public_ip` on port 8000 (cymed/
cycom's backend) or check `/opt/ephemeral/READY` over SSH.

Teardown: `terraform destroy` with the same vars. `preserve_boot_volume =
false` on the instance resource — nothing survives destroy, by design.

**Not exercised against a real OCI account in this session** — written
to the OCI Terraform provider's documented schema, treat as code-complete
needing a real `terraform plan`/`apply` dry run before first real use.

**Known gaps, not built here:**
- No DNS/TLS for the ephemeral instance — reachable by raw IP:8000 only.
  A real "preview URL per branch" would need a wildcard DNS record +
  either per-instance Let's Encrypt or a shared reverse proxy that routes
  by hostname to the right instance's IP.
- No automatic teardown-on-PR-close / idle-timeout — someone (or CI) has
  to run `terraform destroy` explicitly, or these accumulate real cost.
- Single-app only, not a snapshot of a whole multi-app customer
  environment.
