import logging

from celery import shared_task

from . import services

log = logging.getLogger("platform.ephemeral_envs")


@shared_task(name="ephemeral_envs.provision", bind=True, max_retries=0)
def provision_environment_task(self, env_id: str):
    from .models import EphemeralEnvironment

    env = EphemeralEnvironment.objects.get(id=env_id)
    env.status = "provisioning"
    env.save(update_fields=["status", "updated_at"])

    try:
        result = services.provision(name=env.name, app=env.app, git_ref=env.git_ref)
    except services.TerraformNotConfigured as exc:
        env.status, env.error_message = "failed", str(exc)
        env.save(update_fields=["status", "error_message", "updated_at"])
        log.warning("ephemeral env %s not provisioned: %s", env.name, exc)
        return
    except services.TerraformRunError as exc:
        env.status, env.error_message = "failed", f"{exc}\n\n{exc.output}"
        env.save(update_fields=["status", "error_message", "updated_at"])
        log.exception("ephemeral env %s failed to provision", env.name)
        return

    env.status = "ready"
    env.public_ip = result.get("public_ip") or None
    env.terraform_instance_id = result.get("instance_id") or ""
    env.save(update_fields=["status", "public_ip", "terraform_instance_id", "updated_at"])
    log.info("ephemeral env %s ready at %s", env.name, env.public_ip)


@shared_task(name="ephemeral_envs.destroy", bind=True, max_retries=0)
def destroy_environment_task(self, env_id: str):
    from .models import EphemeralEnvironment

    env = EphemeralEnvironment.objects.get(id=env_id)
    env.status = "destroying"
    env.save(update_fields=["status", "updated_at"])

    try:
        services.destroy(name=env.name)
    except (services.TerraformNotConfigured, services.TerraformRunError) as exc:
        env.status, env.error_message = "destroy_failed", str(exc)
        env.save(update_fields=["status", "error_message", "updated_at"])
        log.exception("ephemeral env %s failed to destroy", env.name)
        return

    env.status = "destroyed"
    env.save(update_fields=["status", "updated_at"])
    log.info("ephemeral env %s destroyed", env.name)
