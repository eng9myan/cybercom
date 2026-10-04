from django.apps import AppConfig


class EphemeralEnvsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.ephemeral_envs"
    label = "ephemeral_envs"
    verbose_name = "Ephemeral Environments (Phase 4 hosting)"
