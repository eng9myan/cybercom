from django.urls import include, path

urlpatterns = [
    path("registries/", include("products.cymed.population_health.registries.urls")),
    path("public-health/", include("products.cymed.population_health.public_health.urls")),
    path("surveillance/", include("products.cymed.population_health.surveillance.urls")),
    path("quality/", include("products.cymed.population_health.quality.urls")),
    path("care-gaps/", include("products.cymed.population_health.care_gaps.urls")),
    path("risk/", include("products.cymed.population_health.risk_management.urls")),
    path("cohorts/", include("products.cymed.population_health.cohorts.urls")),
    path("epidemiology/", include("products.cymed.population_health.epidemiology.urls")),
    path("programs/", include("products.cymed.population_health.national_programs.urls")),
    path("analytics/", include("products.cymed.population_health.analytics.urls")),
    path("reporting/", include("products.cymed.population_health.reporting.urls")),
    path("digital-health/", include("products.cymed.population_health.digital_health.urls")),
]
