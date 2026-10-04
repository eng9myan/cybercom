"""
Shells out to the Terraform module in infrastructure/terraform/ephemeral-env/
to actually provision/destroy ephemeral environments. Isolated from the
Django/Celery process itself so a hung `terraform apply` can't wedge a
worker indefinitely without a visible timeout.

Fails honestly (TerraformNotConfigured) when the terraform binary or the
account-specific OCI variables aren't available — same "engine complete,
needs a real account" posture as every other infra integration in this
repo (HyperPay, JoFotara, the e-invoicing national formats, ...). Nothing
here invents a fake success.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger("platform.ephemeral_envs")

MODULE_DIR = Path(__file__).resolve().parent.parent.parent / "infrastructure" / "terraform" / "ephemeral-env"

#: OCI vars with no sensible default — account-specific, read from the
#: environment the Celery worker runs in (never hardcoded, never logged).
_REQUIRED_ENV = (
    "OCI_COMPARTMENT_ID", "OCI_AVAILABILITY_DOMAIN", "OCI_SUBNET_ID",
    "OCI_IMAGE_ID", "OCI_SSH_PUBLIC_KEY",
)


class TerraformNotConfigured(RuntimeError):
    """The terraform binary or the required OCI variables aren't available."""


class TerraformRunError(RuntimeError):
    """`terraform` ran but exited non-zero. `output` carries its stderr/stdout tail."""

    def __init__(self, message: str, output: str):
        super().__init__(message)
        self.output = output


def _check_configured() -> str:
    binary = shutil.which(os.getenv("TERRAFORM_BINARY", "terraform"))
    if not binary:
        raise TerraformNotConfigured(
            "No `terraform` binary on PATH. Install Terraform >= 1.5 (or set TERRAFORM_BINARY to its path) "
            "on the machine running the Celery worker that processes ephemeral-environment jobs."
        )
    missing = [v for v in _REQUIRED_ENV if not os.getenv(v)]
    if missing:
        raise TerraformNotConfigured(
            f"Missing OCI variables: {', '.join(missing)}. These are account-specific (compartment/AD/subnet/"
            "image OCIDs, an SSH public key) — see infrastructure/terraform/ephemeral-env/README.md."
        )
    return binary


def _workspace_dir(name: str) -> Path:
    # A real, separate working directory per environment (not just a
    # `terraform workspace`) — simpler to reason about, and survives a
    # worker restart without needing shared state beyond the filesystem.
    base = Path(os.getenv("TERRAFORM_WORKSPACES_DIR", "/var/lib/cybercom/ephemeral-envs"))
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _run(binary: str, args: list[str], cwd: Path, timeout: int) -> str:
    result = subprocess.run(
        [binary, *args], cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
    )
    tail = (result.stdout or "")[-4000:] + (result.stderr or "")[-4000:]
    if result.returncode != 0:
        raise TerraformRunError(f"terraform {' '.join(args)} exited {result.returncode}", tail)
    return result.stdout


def provision(*, name: str, app: str, git_ref: str, timeout: int = 1800) -> dict:
    """Runs `terraform init` + `apply` for one environment. Returns
    {"public_ip": ..., "instance_id": ...} on success. Raises
    TerraformNotConfigured / TerraformRunError otherwise — never returns a
    fake result."""
    binary = _check_configured()
    workdir = _workspace_dir(name)
    if not (workdir / "main.tf").exists():
        for f in MODULE_DIR.glob("*"):
            if f.is_file():
                (workdir / f.name).write_bytes(f.read_bytes())

    tfvars = workdir / "terraform.tfvars.json"
    tfvars.write_text(json.dumps({
        "compartment_id": os.environ["OCI_COMPARTMENT_ID"],
        "availability_domain": os.environ["OCI_AVAILABILITY_DOMAIN"],
        "subnet_id": os.environ["OCI_SUBNET_ID"],
        "image_id": os.environ["OCI_IMAGE_ID"],
        "ssh_public_key": os.environ["OCI_SSH_PUBLIC_KEY"],
        "environment_name": name,
        "app": app,
        "git_ref": git_ref,
    }))

    logger.info("ephemeral_envs.provision name=%s app=%s git_ref=%s", name, app, git_ref)
    _run(binary, ["init", "-input=false"], workdir, timeout=300)
    _run(binary, ["apply", "-auto-approve", "-input=false"], workdir, timeout=timeout)
    raw = _run(binary, ["output", "-json"], workdir, timeout=60)
    outputs = json.loads(raw)
    return {
        "public_ip": outputs.get("public_ip", {}).get("value"),
        "instance_id": outputs.get("instance_id", {}).get("value"),
    }


def destroy(*, name: str, timeout: int = 900) -> None:
    binary = _check_configured()
    workdir = _workspace_dir(name)
    if not (workdir / "terraform.tfvars.json").exists():
        raise TerraformRunError(f"No Terraform state found for '{name}' at {workdir}", "")
    logger.info("ephemeral_envs.destroy name=%s", name)
    _run(binary, ["destroy", "-auto-approve", "-input=false"], workdir, timeout=timeout)
