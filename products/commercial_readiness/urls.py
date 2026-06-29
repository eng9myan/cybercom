from rest_framework.routers import DefaultRouter

from .views import (
    CommercialMetricsSnapshotViewSet,
    CompetitiveBenchmarkViewSet,
    ComplianceCertificationViewSet,
    ConcurrentLicenseSessionViewSet,
    CustomerPortalAccessViewSet,
    FeatureFlagViewSet,
    LicenseKeyViewSet,
    LicenseViewSet,
    MarketplaceInstallationViewSet,
    MarketplaceListingViewSet,
    PricingPlanViewSet,
    ProductEditionViewSet,
    ProposalViewSet,
    QuotationViewSet,
    SubscriptionViewSet,
    SupportTicketViewSet,
    TenantFeatureFlagOverrideViewSet,
    WhiteLabelConfigViewSet,
)

router = DefaultRouter()
router.register("pricing-plans", PricingPlanViewSet, basename="pricing-plan")
router.register("quotations", QuotationViewSet, basename="quotation")
router.register("proposals", ProposalViewSet, basename="proposal")
router.register("license-keys", LicenseKeyViewSet, basename="license-key")
router.register(
    "compliance-certifications", ComplianceCertificationViewSet, basename="compliance-certification"
)
router.register("benchmarks", CompetitiveBenchmarkViewSet, basename="competitive-benchmark")
router.register("licenses", LicenseViewSet, basename="license")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("product-editions", ProductEditionViewSet, basename="product-edition")
router.register("feature-flags", FeatureFlagViewSet, basename="feature-flag")
router.register(
    "feature-flag-overrides", TenantFeatureFlagOverrideViewSet, basename="feature-flag-override"
)
router.register("white-label-configs", WhiteLabelConfigViewSet, basename="white-label-config")
router.register(
    "concurrent-sessions", ConcurrentLicenseSessionViewSet, basename="concurrent-session"
)
router.register("portal-access", CustomerPortalAccessViewSet, basename="customer-portal-access")
router.register("support-tickets", SupportTicketViewSet, basename="support-ticket")
router.register("marketplace-listings", MarketplaceListingViewSet, basename="marketplace-listing")
router.register(
    "marketplace-installations", MarketplaceInstallationViewSet, basename="marketplace-installation"
)
router.register("metrics-snapshots", CommercialMetricsSnapshotViewSet, basename="metrics-snapshot")

urlpatterns = router.urls
