from django.urls import include, path

urlpatterns = [
    path("reception/", include("products.cymed.clinic.reception.urls")),
    path("appointments/", include("products.cymed.clinic.appointments.urls")),
    path("consultations/", include("products.cymed.clinic.consultations.urls")),
    path("triage/", include("products.cymed.clinic.triage.urls")),
    path("telemedicine/", include("products.cymed.clinic.telemedicine.urls")),
    path("referrals/", include("products.cymed.clinic.referrals.urls")),
    path("queues/", include("products.cymed.clinic.queues.urls")),
    path("specialties/", include("products.cymed.clinic.specialties.urls")),
    path("forms/", include("products.cymed.clinic.clinical_forms.urls")),
    path("billing/", include("products.cymed.clinic.billing_bridge.urls")),
    path("insurance/", include("products.cymed.clinic.insurance_bridge.urls")),
]
