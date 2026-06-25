from rest_framework.routers import DefaultRouter
from .views import (
    PricingPlanViewSet, QuotationViewSet, ProposalViewSet, LicenseKeyViewSet,
    ComplianceCertificationViewSet, CompetitiveBenchmarkViewSet,
)

router = DefaultRouter()
router.register("pricing-plans", PricingPlanViewSet, basename="pricing-plan")
router.register("quotations", QuotationViewSet, basename="quotation")
router.register("proposals", ProposalViewSet, basename="proposal")
router.register("license-keys", LicenseKeyViewSet, basename="license-key")
router.register("compliance-certifications", ComplianceCertificationViewSet, basename="compliance-certification")
router.register("benchmarks", CompetitiveBenchmarkViewSet, basename="competitive-benchmark")

urlpatterns = router.urls
