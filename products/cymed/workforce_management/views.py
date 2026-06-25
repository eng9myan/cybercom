from django.http import JsonResponse

WORKFORCE_MANAGEMENT_EDITIONS = {
    "standard": [
        "workforce_profiles",
        "scheduling",
        "shift_swaps",
        "float_pool",
        "acuity",
        "oncall",
        "compliance",
        "fatigue",
    ],
    "enterprise": [
        "workforce_profiles",
        "scheduling",
        "shift_swaps",
        "float_pool",
        "acuity",
        "oncall",
        "compliance",
        "fatigue",
        "forecasting",
        "analytics",
    ],
    "academic_medical_center": [
        "workforce_profiles",
        "scheduling",
        "shift_swaps",
        "float_pool",
        "acuity",
        "oncall",
        "compliance",
        "fatigue",
        "forecasting",
        "analytics",
        "acgme_residency_gates",
        "research_block_scheduling",
    ],
    "government": [
        "workforce_profiles",
        "scheduling",
        "shift_swaps",
        "float_pool",
        "acuity",
        "oncall",
        "compliance",
        "fatigue",
        "forecasting",
        "analytics",
        "ramadan_rules",
        "civil_service_rosters",
        "government_procurement_integration",
    ],
}


def hwm_health(request):
    return JsonResponse({"status": "ok", "service": "cymed_workforce_management"})


def hwm_editions(request):
    return JsonResponse({"editions": WORKFORCE_MANAGEMENT_EDITIONS})
