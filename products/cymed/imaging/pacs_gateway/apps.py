from django.apps import AppConfig


class PACSGatewayConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.imaging.pacs_gateway"
    label = "img_pacs"
    verbose_name = "CyMed Imaging — PACS Gateway"
