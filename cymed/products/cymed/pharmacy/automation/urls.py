"""Automation URL routing."""

from rest_framework.routers import DefaultRouter

from .views import (
    AutomationDeviceViewSet,
    AutomationQueueViewSet,
    CabinetDeviceViewSet,
    DispensingRobotViewSet,
)

router = DefaultRouter()
router.register(r"devices", AutomationDeviceViewSet, basename="automation-device")
router.register(r"robots", DispensingRobotViewSet, basename="dispensing-robot")
router.register(r"cabinets", CabinetDeviceViewSet, basename="cabinet-device")
router.register(r"queue", AutomationQueueViewSet, basename="automation-queue")

urlpatterns = router.urls
