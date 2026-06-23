from django.urls import path
from products.cymed.hospital.clinical_command_center.views import ClinicalCommandCenterMetricsView

urlpatterns = [
    path("metrics/", ClinicalCommandCenterMetricsView.as_view(), name="command-center-metrics"),
]
