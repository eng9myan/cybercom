# ============================================================
# Ephemeral per-branch/per-tenant environment — Phase 4 (Odoo.sh-equivalent
# hosting), item 2: the IaC layer behind platform.ephemeral_envs' API.
#
# Provisions ONE throwaway OCI compute instance that clones the repo at
# `git_ref`, builds the chosen app's existing production Docker image
# (infrastructure/Dockerfile.cymed or .cycom) and brings it up via the
# same docker-compose.*-api.yml already used by deploy-production.sh —
# deliberately NOT a parallel deploy mechanism, so an ephemeral env
# behaves like production for testing purposes. Each environment is
# fully self-contained (own VM, own Postgres/Redis/Keycloak containers)
# — no attempt to share infra across environments, trading some cost
# efficiency for zero cross-environment blast radius.
#
# NOT exercised against a real OCI account in this session (none
# available) — written to the current OCI Terraform provider's
# documented resource schema, but treat as code-complete / needs a real
# `terraform plan` on a real account before first use, same caveat as
# every other "engine complete, needs real infra" item in this repo.
# ============================================================

terraform {
  required_version = ">= 1.5"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

locals {
  env_name       = "${var.app}-ephemeral-${var.environment_name}"
  compose_file   = var.app == "cymed" ? "docker-compose.api.yml" : "docker-compose.cycom-api.yml"
  dockerfile     = var.app == "cymed" ? "infrastructure/Dockerfile.cymed" : "infrastructure/Dockerfile.cycom"
}

resource "oci_core_instance" "this" {
  compartment_id      = var.compartment_id
  availability_domain = var.availability_domain
  display_name        = local.env_name
  shape               = var.shape

  dynamic "shape_config" {
    for_each = can(regex("Flex$", var.shape)) ? [1] : []
    content {
      ocpus         = var.shape_ocpus
      memory_in_gbs = var.shape_memory_gbs
    }
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = true
    display_name     = "${local.env_name}-vnic"
  }

  source_details {
    source_type = "image"
    source_id   = var.image_id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(templatefile("${path.module}/cloud-init.yaml.tftpl", {
      app          = var.app
      git_ref      = var.git_ref
      repo_url     = var.repo_url
      compose_file = local.compose_file
      dockerfile   = local.dockerfile
      env_name     = local.env_name
    }))
  }

  freeform_tags = {
    "cybercom:ephemeral"   = "true"
    "cybercom:app"         = var.app
    "cybercom:environment" = var.environment_name
  }

  # Ephemeral by design — a destroy should never prompt or wait on
  # anything, this instance holds no data worth preserving once the
  # environment it was created for (a PR, a trial tenant) is gone.
  preserve_boot_volume = false
}
