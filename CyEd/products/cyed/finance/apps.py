from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyed.finance"
    label = "cyed_finance"
    verbose_name = "CyEd — Finance (General Ledger)"
