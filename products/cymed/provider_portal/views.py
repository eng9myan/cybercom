from django.http import JsonResponse

PROVIDER_EDITIONS = {
    "standard": [
        "workspace",
        "patient_lists",
        "clinical_tasks",
        "results",
        "clinical_documentation",
    ],
    "enterprise": [
        "workspace",
        "patient_lists",
        "clinical_tasks",
        "results",
        "clinical_documentation",
        "care_team",
        "telemedicine",
        "clinical_messaging",
        "analytics",
        "mobile",
        "orders",
        "rounding",
        "approvals",
    ],
    "academic_medical_center": [
        "workspace",
        "patient_lists",
        "clinical_tasks",
        "results",
        "clinical_documentation",
        "care_team",
        "telemedicine",
        "clinical_messaging",
        "analytics",
        "mobile",
        "orders",
        "rounding",
        "approvals",
        "workforce",
        "teaching_teams",
        "research_workflows",
        "training_analytics",
        "resident_management",
    ],
    "government_workforce": [
        "workspace",
        "patient_lists",
        "clinical_tasks",
        "results",
        "clinical_documentation",
        "care_team",
        "telemedicine",
        "clinical_messaging",
        "analytics",
        "mobile",
        "orders",
        "rounding",
        "approvals",
        "workforce",
        "national_workforce_management",
        "regional_assignments",
        "public_health_workforce_analytics",
    ],
}


def portal_health(request):
    return JsonResponse({"status": "ok", "service": "cymed_provider_portal"})


def portal_editions(request):
    return JsonResponse({"editions": PROVIDER_EDITIONS})
