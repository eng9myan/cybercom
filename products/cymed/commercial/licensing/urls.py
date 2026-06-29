from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.licensing.views import (
    LicenseActivationViewSet,
    LicenseAuditViewSet,
    LicenseFeatureViewSet,
    LicenseKeyViewSet,
    LicenseServerViewSet,
    LicenseUsageViewSet,
    LicenseViewSet,
    OfflineActivationPackageViewSet,
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
