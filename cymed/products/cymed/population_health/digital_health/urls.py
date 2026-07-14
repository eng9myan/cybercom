from rest_framework.routers import DefaultRouter

from .views import (
    DigitalHealthWalletEntryViewSet,
    HealthPassViewSet,
    NationalHealthIDViewSet,
    VaccinationCertificateViewSet,
)

router = DefaultRouter()
router.register(r"national-ids", NationalHealthIDViewSet, basename="national-health-id")
router.register(
    r"vaccination-certificates", VaccinationCertificateViewSet, basename="vaccination-certificate"
)
router.register(r"health-passes", HealthPassViewSet, basename="health-pass")
router.register(r"wallet-entries", DigitalHealthWalletEntryViewSet, basename="wallet-entry")

urlpatterns = router.urls
