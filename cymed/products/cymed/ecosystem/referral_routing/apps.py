"""AppConfig for CyMed Ecosystem cross-provider referral routing sub-app."""
from django.apps import AppConfig


class ReferralRoutingConfig(AppConfig):
    name = "products.cymed.ecosystem.referral_routing"
    label = "cymed_eco_referral_routing"
    verbose_name = "CyMed Ecosystem — Cross-Provider Referral Routing"
