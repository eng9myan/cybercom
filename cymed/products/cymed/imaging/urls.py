from django.urls import include, path

urlpatterns = [
    path("orders/", include("products.cymed.imaging.orders.urls")),
    path("scheduling/", include("products.cymed.imaging.scheduling.urls")),
    path("worklist/", include("products.cymed.imaging.modality_worklist.urls")),
    path("reporting/", include("products.cymed.imaging.radiology_reporting.urls")),
    path("results/", include("products.cymed.imaging.results.urls")),
    path("pacs/", include("products.cymed.imaging.pacs_gateway.urls")),
    path("dicom/", include("products.cymed.imaging.dicom_registry.urls")),
    path("teleradiology/", include("products.cymed.imaging.teleradiology.urls")),
    path("quality/", include("products.cymed.imaging.quality.urls")),
    path("analytics/", include("products.cymed.imaging.analytics.urls")),
    # ── Gap-fill (P0-11) ───────────────────────────────────────────
    path("booking/",          include("products.cymed.imaging.patient_booking.urls")),
    path("patient-results/",  include("products.cymed.imaging.patient_results.urls")),
    path("sharing/",          include("products.cymed.imaging.image_sharing.urls")),
    path("ai-triage/",        include("products.cymed.imaging.ai_triage.urls")),
    path("telerad-market/",   include("products.cymed.imaging.tele_marketplace.urls")),
    path("prep/",             include("products.cymed.imaging.prep_instructions.urls")),
]
