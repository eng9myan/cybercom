from django.apps import AppConfig


class GovernanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyed.governance"
    label = "cyed_governance"
    verbose_name = "CyEd — Governance (RBAC, Consent, Audit)"
