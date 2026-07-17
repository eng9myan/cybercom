from django.apps import AppConfig


class PosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.pos"
    label = "cycom_pos"
    verbose_name = "Cycom — POS"
