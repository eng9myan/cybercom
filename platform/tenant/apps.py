from django.apps import AppConfig


class TenantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.tenant"
    label = "platform_tenant"
    verbose_name = "Platform Tenant"
