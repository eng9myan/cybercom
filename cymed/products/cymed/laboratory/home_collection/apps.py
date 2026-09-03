"""AppConfig for the CyMed Laboratory home_collection sub-app."""

from django.apps import AppConfig


class HomeCollectionConfig(AppConfig):
    name = "products.cymed.laboratory.home_collection"
    label = "cymed_lab_home_collection"
    verbose_name = "CyMed Laboratory — Home Sample Collection"
