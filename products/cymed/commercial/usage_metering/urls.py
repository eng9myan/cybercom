from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.usage_metering.views import (
    UsageAlertViewSet,
    UsageDashboardView,
    UsageMeterViewSet,
)

router = DefaultRouter()
router.register("meters", UsageMeterViewSet)
router.register("alerts", UsageAlertViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", UsageDashboardView.as_view(), name="usage-dashboard"),
]
