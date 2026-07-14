from django.apps import AppConfig


class TeleradiologyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.imaging.teleradiology"
    label = "img_teleradiology"
    verbose_name = "CyMed Imaging — Teleradiology"
