from django.apps import AppConfig


class ProductCatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.commercial.product_catalog"
    label = "commercial_product_catalog"
    verbose_name = "CyMed Commercial — Product Catalog"
