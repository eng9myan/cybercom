from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Hosts cross-cutting infrastructure: crypto, permissions, viewset bases and
    the deployment checks.

    Registered as an app purely so `ready()` runs — `core.checks` uses the
    check framework's `@register` decorator, which does nothing unless the
    module is imported. A security check that is never loaded is worse than
    none, because it looks like coverage.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    label = "cyed_core"
    verbose_name = "CyEd — Core"

    def ready(self):
        from core import checks  # noqa: F401
