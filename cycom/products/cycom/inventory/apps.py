from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.inventory"
    label = "cycom_inventory"
    verbose_name = "Cycom — Inventory"
