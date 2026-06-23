from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.provider_portal.analytics"
    label = "cymed_provider_analytics"
    verbose_name = "CyMed Provider Analytics"
