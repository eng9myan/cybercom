from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.usage_metering.views import (
    UsageMeterViewSet, UsageAlertViewSet, UsageDashboardView
)

router = DefaultRouter()
router.register("meters", UsageMeterViewSet)
router.register("alerts", UsageAlertViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", UsageDashboardView.as_view(), name="usage-dashboard"),
]
