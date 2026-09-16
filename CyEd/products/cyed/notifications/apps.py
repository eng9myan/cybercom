from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyed.notifications"
    label = "cyed_notifications"
    verbose_name = "CyEd — Notifications"

    def ready(self):
        # Connect the absence → guardian notification trigger.
        from products.cyed.notifications import signals  # noqa: F401
