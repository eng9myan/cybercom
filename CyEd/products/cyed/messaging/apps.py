from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyed.messaging"
    label = "cyed_messaging"
    verbose_name = "CyEd — Two-way Messaging"
