from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.catalog"
    label = "cycom_catalog"
    verbose_name = "Cycom — Catalog"
