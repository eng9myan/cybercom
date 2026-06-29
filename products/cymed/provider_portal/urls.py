from django.urls import include, path

urlpatterns = [
    path("workspace/", include("products.cymed.provider_portal.workspace.urls")),
    path("patient-lists/", include("products.cymed.provider_portal.patient_lists.urls")),
    path("tasks/", include("products.cymed.provider_portal.clinical_tasks.urls")),
    path("messaging/", include("products.cymed.provider_portal.clinical_messaging.urls")),
    path("workforce/", include("products.cymed.provider_portal.workforce.urls")),
    path("rounds/", include("products.cymed.provider_portal.rounding.urls")),
    path("orders/", include("products.cymed.provider_portal.orders.urls")),
    path("results/", include("products.cymed.provider_portal.results.urls")),
    path("documentation/", include("products.cymed.provider_portal.clinical_documentation.urls")),
    path("telemedicine/", include("products.cymed.provider_portal.telemedicine.urls")),
    path("care-teams/", include("products.cymed.provider_portal.care_team.urls")),
    path("approvals/", include("products.cymed.provider_portal.approvals.urls")),
    path("analytics/", include("products.cymed.provider_portal.analytics.urls")),
    path("mobile/", include("products.cymed.provider_portal.mobile.urls")),
]
