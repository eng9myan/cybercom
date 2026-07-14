from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"wallets", views.HealthWalletViewSet, basename="health-wallet")
router.register(r"cards", views.DigitalCardViewSet, basename="digital-card")
router.register(r"passes", views.HealthPassViewSet, basename="health-pass")
router.register(r"vaccinations", views.VaccinationRecordViewSet, basename="vaccination-record")

urlpatterns = [
    path("", include(router.urls)),
]
