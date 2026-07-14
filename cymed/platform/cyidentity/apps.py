from django.apps import AppConfig


class CyIdentityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.cyidentity"
    label = "platform_cyidentity"
    verbose_name = "CyIdentity"

    def ready(self) -> None:  # pragma: no cover
        # Wire signal handlers
        from platform.cyidentity import signals  # noqa: F401
