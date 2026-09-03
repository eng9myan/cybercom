"""App config for CyMed ecosystem-wide loyalty and rewards."""
from django.apps import AppConfig


class RewardsConfig(AppConfig):
    name = "products.cymed.ecosystem.rewards"
    label = "cymed_eco_rewards"
    verbose_name = "CyMed Ecosystem — Ecosystem-wide Loyalty & Rewards"
