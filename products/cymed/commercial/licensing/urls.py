from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.licensing.views import (
    LicenseViewSet, LicenseKeyViewSet, LicenseActivationViewSet,
    LicenseFeatureViewSet, LicenseAuditViewSet, LicenseUsageViewSet,
    LicenseServerViewSet, OfflineActivationPackageViewSet
)

router = DefaultRouter()
router.register("licenses", LicenseViewSet)
router.register("keys", LicenseKeyViewSet)
router.register("activations", LicenseActivationViewSet)
router.register("features", LicenseFeatureViewSet)
router.register("audit", LicenseAuditViewSet)
router.register("usage", LicenseUsageViewSet)
router.register("servers", LicenseServerViewSet)
router.register("offline-packages", OfflineActivationPackageViewSet)

urlpatterns = [path("", include(router.urls))]
