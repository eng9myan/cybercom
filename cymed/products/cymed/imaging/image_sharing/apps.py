"""AppConfig for the CyMed Imaging image_sharing sub-app."""
from django.apps import AppConfig


class ImageSharingConfig(AppConfig):
    name = "products.cymed.imaging.image_sharing"
    label = "cymed_img_image_sharing"
    verbose_name = "CyMed Imaging - Digital Image Sharing (CD replacement)"
