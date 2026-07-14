from django.http import JsonResponse

RCM_EDITIONS = {
    "standard": [
        "eligibility",
        "insurance",
        "billing",
        "claims",
    ],
    "enterprise": [
        "eligibility",
        "insurance",
        "preauthorization",
        "billing",
        "charge_capture",
        "claims",
        "denials",
        "collections",
        "contracts",
        "pricing",
        "revenue_analytics",
        "payer_portal",
    ],
    "government_payer": [
        "eligibility",
        "insurance",
        "preauthorization",
        "billing",
        "charge_capture",
        "claims",
        "denials",
        "collections",
        "contracts",
        "pricing",
        "revenue_analytics",
        "payer_portal",
        "national_insurance_programs",
        "government_claims",
        "public_health_funding_models",
    ],
}


def rcm_health(request):
    return JsonResponse({"status": "ok", "service": "cymed_rcm"})


def rcm_editions(request):
    return JsonResponse({"editions": RCM_EDITIONS})
