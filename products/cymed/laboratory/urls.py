"""
CyMed Laboratory — API URL configuration.
Mounted at: /api/v1/lab/
"""
from django.urls import path, include

urlpatterns = [
    path("orders/", include("products.cymed.laboratory.orders.urls")),
    path("specimens/", include("products.cymed.laboratory.specimens.urls")),
    path("accessioning/", include("products.cymed.laboratory.accessioning.urls")),
    path("worklists/", include("products.cymed.laboratory.worklists.urls")),
    path("results/", include("products.cymed.laboratory.results.urls")),
    path("microbiology/", include("products.cymed.laboratory.microbiology.urls")),
    path("pathology/", include("products.cymed.laboratory.pathology.urls")),
    path("histopathology/", include("products.cymed.laboratory.histopathology.urls")),
    path("quality/", include("products.cymed.laboratory.quality.urls")),
    path("blood-bank/", include("products.cymed.laboratory.blood_bank_foundation.urls")),
    path("analytics/", include("products.cymed.laboratory.analytics.urls")),
    path("reference/", include("products.cymed.laboratory.reference_lab.urls")),
]
