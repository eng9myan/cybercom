import os

from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.common"
    label = "platform_common"
    verbose_name = "Platform Common"
    path = os.path.dirname(os.path.abspath(__file__))
