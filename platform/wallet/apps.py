from django.apps import AppConfig


class WalletConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.wallet"
    label = "platform_wallet"
    verbose_name = "CyID Wallet (stored value)"
