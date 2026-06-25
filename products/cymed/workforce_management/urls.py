from django.urls import path, include

urlpatterns = [
    path("profiles/", include("products.cymed.workforce_management.workforce_profiles.urls")),
    path("scheduling/", include("products.cymed.workforce_management.scheduling.urls")),
    path("shift-swaps/", include("products.cymed.workforce_management.shift_swaps.urls")),
    path("float-pool/", include("products.cymed.workforce_management.float_pool.urls")),
    path("acuity/", include("products.cymed.workforce_management.acuity.urls")),
    path("oncall/", include("products.cymed.workforce_management.oncall.urls")),
    path("compliance/", include("products.cymed.workforce_management.compliance.urls")),
    path("fatigue/", include("products.cymed.workforce_management.fatigue.urls")),
    path("forecasting/", include("products.cymed.workforce_management.forecasting.urls")),
    path("analytics/", include("products.cymed.workforce_management.analytics.urls")),
]
