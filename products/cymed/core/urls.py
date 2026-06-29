from django.urls import include, path

urlpatterns = [
    path("patients/", include("products.cymed.core.patients.urls")),
    path("providers/", include("products.cymed.core.providers.urls")),
    path("organizations/", include("products.cymed.core.organizations.urls")),
    path("facilities/", include("products.cymed.core.facilities.urls")),
    path("encounters/", include("products.cymed.core.encounters.urls")),
    path("clinical/", include("products.cymed.core.clinical.urls")),
    path("documents/", include("products.cymed.core.documents.urls")),
    path("careplans/", include("products.cymed.core.careplans.urls")),
    path("orders/", include("products.cymed.core.orders.urls")),
    path("scheduling/", include("products.cymed.core.scheduling.urls")),
    path("consents/", include("products.cymed.core.consents.urls")),
    path("registries/", include("products.cymed.core.registries.urls")),
]
