from django.urls import path, include
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.results.views import (
    ProviderResultViewViewSet,
    ResultTrendViewSet,
    CriticalResultAlertViewSet,
    ResultAcknowledgementViewSet,
)

router = DefaultRouter()
router.register(r"results", ProviderResultViewViewSet, basename="provider-result")
router.register(r"trends", ResultTrendViewSet, basename="result-trend")
router.register(r"critical-alerts", CriticalResultAlertViewSet, basename="critical-result-alert")
router.register(r"acknowledgements", ResultAcknowledgementViewSet, basename="result-acknowledgement")

urlpatterns = [
    path("", include(router.urls)),
]
