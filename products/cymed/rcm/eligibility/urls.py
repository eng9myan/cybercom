from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EligibilityRequestViewSet,
    EligibilityResponseViewSet,
    CoverageVerificationViewSet,
    BenefitVerificationViewSet,
)

router = DefaultRouter()
router.register(r"eligibility-requests", EligibilityRequestViewSet, basename="eligibility-request")
router.register(r"eligibility-responses", EligibilityResponseViewSet, basename="eligibility-response")
router.register(r"coverage-verifications", CoverageVerificationViewSet, basename="coverage-verification")
router.register(r"benefit-verifications", BenefitVerificationViewSet, basename="benefit-verification")

urlpatterns = [
    path("", include(router.urls)),
]
