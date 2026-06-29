from django.apps import AppConfig


class RiskManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.risk_management"
    label = "cymed_ph_risk_management"
    verbose_name = "CyMed Population Health — Risk Management"
