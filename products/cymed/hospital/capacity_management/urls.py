from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.hospital.capacity_management.views import (
    CapacityRuleViewSet, CapacityThresholdViewSet, SurgePlanViewSet,
    OverflowUnitViewSet
)

router = DefaultRouter()
router.register("rules", CapacityRuleViewSet)
router.register("thresholds", CapacityThresholdViewSet)
router.register("surge-plans", SurgePlanViewSet)
router.register("overflow-units", OverflowUnitViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
