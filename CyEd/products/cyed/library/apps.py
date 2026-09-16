from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyed.library"
    label = "cyed_library"
    verbose_name = "CyEd — Library"
