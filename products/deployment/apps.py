from django.apps import AppConfig


class DeploymentPlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.deployment"
    label = "cybercom_deployment"
    verbose_name = "CyberCom Deployment Platform"
