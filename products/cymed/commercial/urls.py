from django.urls import path, include

urlpatterns = [
    path("licensing/", include("products.cymed.commercial.licensing.urls")),
    path("editions/", include("products.cymed.commercial.editions.urls")),
    path("subscriptions/", include("products.cymed.commercial.subscriptions.urls")),
    path("features/", include("products.cymed.commercial.feature_flags.urls")),
    path("branding/", include("products.cymed.commercial.branding.urls")),
    path("deployments/", include("products.cymed.commercial.deployment_profiles.urls")),
    path("catalog/", include("products.cymed.commercial.product_catalog.urls")),
    path("usage/", include("products.cymed.commercial.usage_metering.urls")),
    path("customers/", include("products.cymed.commercial.customer_management.urls")),
    path("partners/", include("products.cymed.commercial.partner_management.urls")),
]
