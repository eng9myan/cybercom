from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.audit"
    label = "platform_audit"
    verbose_name = "Platform Audit"

    def ready(self):
        import platform.audit.signals  # noqa: F401
