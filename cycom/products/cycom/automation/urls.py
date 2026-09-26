from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.automation.views import (
    AutomationCatalogView,
    AutomationRuleViewSet,
    AutomationRunViewSet,
)

router = DefaultRouter()
router.register("rules", AutomationRuleViewSet, basename="automation-rule")
router.register("runs", AutomationRunViewSet, basename="automation-run")

urlpatterns = [
    path("catalog/", AutomationCatalogView.as_view(), name="automation-catalog"),
    path("", include(router.urls)),
]
