"""CyMed MRFF (Australian priorities) — API URL configuration. Mounted at: /api/v1/mrff/"""
from django.urls import include, path

urlpatterns = [
    path("ai-diagnostics/",    include("products.cymed.mrff.ai_diagnostics.urls")),
    path("offline-kit/",       include("products.cymed.mrff.offline_kit.urls")),
    path("ambient-scribe/",    include("products.cymed.mrff.ambient_scribe.urls")),
    path("population-health/", include("products.cymed.mrff.population_health.urls")),
]
