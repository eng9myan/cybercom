from django.urls import include, path

urlpatterns = [
    path("eligibility/", include("products.cymed.rcm.eligibility.urls")),
    path("insurance/", include("products.cymed.rcm.insurance.urls")),
    path("preauthorization/", include("products.cymed.rcm.preauthorization.urls")),
    path("billing/", include("products.cymed.rcm.billing.urls")),
    path("charge-capture/", include("products.cymed.rcm.charge_capture.urls")),
    path("claims/", include("products.cymed.rcm.claims.urls")),
    path("denials/", include("products.cymed.rcm.denials.urls")),
    path("collections/", include("products.cymed.rcm.collections.urls")),
    path("contracts/", include("products.cymed.rcm.contracts.urls")),
    path("pricing/", include("products.cymed.rcm.pricing.urls")),
    path("analytics/", include("products.cymed.rcm.revenue_analytics.urls")),
    path("payer-portal/", include("products.cymed.rcm.payer_portal.urls")),
]
