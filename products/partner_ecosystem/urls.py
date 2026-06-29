from rest_framework.routers import DefaultRouter

from .views import (
    LeadRegistrationViewSet,
    MarketplaceExtensionViewSet,
    PartnerApplicationViewSet,
    PartnerCertificationViewSet,
    PartnerPortalAccessViewSet,
    PartnerViewSet,
)

router = DefaultRouter()
router.register("partners", PartnerViewSet, basename="partner")
router.register("applications", PartnerApplicationViewSet, basename="partner-application")
router.register("certifications", PartnerCertificationViewSet, basename="partner-certification")
router.register("lead-registrations", LeadRegistrationViewSet, basename="lead-registration")
router.register("marketplace", MarketplaceExtensionViewSet, basename="marketplace-extension")
router.register("portal-access", PartnerPortalAccessViewSet, basename="partner-portal-access")

urlpatterns = router.urls
