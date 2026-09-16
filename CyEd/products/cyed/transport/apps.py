from django.apps import AppConfig


class TransportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyed.transport"
    label = "cyed_transport"
    verbose_name = "CyEd — Transport & Fleet"

    def ready(self):
        from products.cyed.transport import signals  # noqa: F401
