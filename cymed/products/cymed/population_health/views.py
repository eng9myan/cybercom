from django.http import JsonResponse

POPULATION_HEALTH_EDITIONS = {
    "population_health": [
        "registries",
        "care_gaps",
        "cohorts",
        "risk_management",
        "quality",
        "analytics",
    ],
    "public_health": [
        "registries",
        "care_gaps",
        "cohorts",
        "risk_management",
        "quality",
        "analytics",
        "surveillance",
        "epidemiology",
        "reporting",
    ],
    "national_health_platform": [
        "registries",
        "care_gaps",
        "cohorts",
        "risk_management",
        "quality",
        "analytics",
        "surveillance",
        "epidemiology",
        "reporting",
        "public_health",
        "national_programs",
        "digital_health",
    ],
    "government_digital_health": [
        "registries",
        "care_gaps",
        "cohorts",
        "risk_management",
        "quality",
        "analytics",
        "surveillance",
        "epidemiology",
        "reporting",
        "public_health",
        "national_programs",
        "digital_health",
        "ministry_dashboards",
        "cross_agency_integration",
        "citizen_health_services",
    ],
}


def ph_health(request):
    return JsonResponse({"status": "ok", "service": "cymed_population_health"})


def ph_editions(request):
    return JsonResponse({"editions": POPULATION_HEALTH_EDITIONS})
