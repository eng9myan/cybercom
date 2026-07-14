from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BenefitViewSet,
    CoverageRuleViewSet,
    CoverageViewSet,
    InsuranceCardViewSet,
    InsuranceCompanyViewSet,
    InsuranceMemberViewSet,
    InsurancePlanViewSet,
)

router = DefaultRouter()
router.register(r"companies", InsuranceCompanyViewSet, basename="insurance-company")
router.register(r"plans", InsurancePlanViewSet, basename="insurance-plan")
router.register(r"members", InsuranceMemberViewSet, basename="insurance-member")
router.register(r"coverages", CoverageViewSet, basename="insurance-coverage")
router.register(r"benefits", BenefitViewSet, basename="insurance-benefit")
router.register(r"coverage-rules", CoverageRuleViewSet, basename="insurance-coverage-rule")
router.register(r"cards", InsuranceCardViewSet, basename="insurance-card")

urlpatterns = [
    path("", include(router.urls)),
]
