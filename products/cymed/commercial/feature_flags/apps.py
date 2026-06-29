from django.apps import AppConfig


class FeatureFlagsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.commercial.feature_flags"
    label = "commercial_feature_flags"
    verbose_name = "CyMed Commercial — Feature Flags"
