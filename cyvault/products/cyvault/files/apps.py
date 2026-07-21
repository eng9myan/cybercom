from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyvault.files"
    label = "cyvault_files"
    verbose_name = "CyVault — Files"
