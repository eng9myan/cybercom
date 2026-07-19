from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.scheduler"
    label = "cycom_scheduler"
    verbose_name = "Cycom — Calendar"
