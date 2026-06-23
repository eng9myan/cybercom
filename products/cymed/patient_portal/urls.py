"""
CyMed Patient Portal — Package-Level URL Router
Routes requests to each portal app.
"""
from django.urls import path, include

urlpatterns = [
    path("accounts/", include("products.cymed.patient_portal.accounts.urls")),
    path("directory/", include("products.cymed.patient_portal.directory.urls")),
    path("appointments/", include("products.cymed.patient_portal.appointments.urls")),
    path("telemedicine/", include("products.cymed.patient_portal.telemedicine.urls")),
    path("medical-records/", include("products.cymed.patient_portal.medical_records.urls")),
    path("lab-results/", include("products.cymed.patient_portal.laboratory_results.urls")),
    path("imaging-results/", include("products.cymed.patient_portal.imaging_results.urls")),
    path("prescriptions/", include("products.cymed.patient_portal.prescriptions.urls")),
    path("payments/", include("products.cymed.patient_portal.payments.urls")),
    path("insurance/", include("products.cymed.patient_portal.insurance.urls")),
    path("messaging/", include("products.cymed.patient_portal.messaging.urls")),
    path("notifications/", include("products.cymed.patient_portal.notifications.urls")),
    path("family/", include("products.cymed.patient_portal.family_accounts.urls")),
    path("consents/", include("products.cymed.patient_portal.consents.urls")),
    path("wallet/", include("products.cymed.patient_portal.wallet.urls")),
    path("health-journey/", include("products.cymed.patient_portal.health_journey.urls")),
]
