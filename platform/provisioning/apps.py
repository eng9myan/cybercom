from django.apps import AppConfig


class ProvisioningConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.provisioning"
    label = "provisioning"
    verbose_name = "Cycom Ready-ERP Provisioning"
