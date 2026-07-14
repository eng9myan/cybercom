"""
CyMed Patient Portal — Package-Level Views
Portal health check and feature edition map.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

PORTAL_EDITIONS = {
    "cymed_patient_portal_standard": [
        "appointments",
        "medical_records",
        "laboratory_results",
        "imaging_results",
        "prescriptions",
        "directory",
        "notifications",
        "consents",
    ],
    "cymed_patient_portal_enterprise": [
        "appointments",
        "medical_records",
        "laboratory_results",
        "imaging_results",
        "prescriptions",
        "directory",
        "notifications",
        "consents",
        "telemedicine",
        "messaging",
        "wallet",
        "payments",
        "insurance",
        "family_accounts",
        "health_journey",
    ],
    "cymed_patient_portal_government": [
        "appointments",
        "medical_records",
        "laboratory_results",
        "imaging_results",
        "prescriptions",
        "directory",
        "notifications",
        "consents",
        "telemedicine",
        "messaging",
        "wallet",
        "payments",
        "insurance",
        "family_accounts",
        "health_journey",
        "national_id_integration",
        "national_health_wallet",
        "public_health_programs",
    ],
    "cymed_national_digital_health_portal": [
        "appointments",
        "medical_records",
        "laboratory_results",
        "imaging_results",
        "prescriptions",
        "directory",
        "notifications",
        "consents",
        "telemedicine",
        "messaging",
        "wallet",
        "payments",
        "insurance",
        "family_accounts",
        "health_journey",
        "national_id_integration",
        "national_health_wallet",
        "public_health_programs",
        "multi_provider_network",
        "national_analytics",
        "federated_identity",
    ],
}


@api_view(["GET"])
@permission_classes([AllowAny])
def portal_health(request):
    return Response({"status": "ok", "product": "CyMed Patient Portal", "version": "3.6"})


@api_view(["GET"])
@permission_classes([AllowAny])
def portal_editions(request):
    return Response(PORTAL_EDITIONS)
