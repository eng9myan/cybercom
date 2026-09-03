"""AppConfig for CyMed Imaging patient prep instructions sub-app."""
from django.apps import AppConfig


class PrepInstructionsConfig(AppConfig):
    name = "products.cymed.imaging.prep_instructions"
    label = "cymed_img_prep_instructions"
    verbose_name = "CyMed Imaging — Patient Prep Instructions"
