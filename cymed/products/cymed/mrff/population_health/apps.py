"""Django app config for CyMed MRFF population health sub-app."""
from django.apps import AppConfig


class PopulationHealthConfig(AppConfig):
    name = "products.cymed.mrff.population_health"
    label = "cymed_mrff_population_health"
    verbose_name = "CyMed MRFF — Population Health & Registries"
