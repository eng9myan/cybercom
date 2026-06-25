from django.apps import AppConfig


class FloatPoolConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.workforce_management.float_pool"
    label = "cymed_hwm_float_pool"
    verbose_name = "CyMed Workforce Management — Float Pool"
