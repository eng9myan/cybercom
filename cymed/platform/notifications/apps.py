from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.notifications"
    label = "platform_notifications"
    verbose_name = "Platform Notifications"
