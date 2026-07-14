from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.capacity_management.views import (
    CapacityRuleViewSet,
    CapacityThresholdViewSet,
    OverflowUnitViewSet,
    SurgePlanViewSet,
)

router = DefaultRouter()
router.register("rules", CapacityRuleViewSet)
router.register("thresholds", CapacityThresholdViewSet)
router.register("surge-plans", SurgePlanViewSet)
router.register("overflow-units", OverflowUnitViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
