"""Automation URL routing."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AutomationDeviceViewSet, DispensingRobotViewSet, CabinetDeviceViewSet, AutomationQueueViewSet

router = DefaultRouter()
router.register(r"devices", AutomationDeviceViewSet, basename="automation-device")
router.register(r"robots", DispensingRobotViewSet, basename="dispensing-robot")
router.register(r"cabinets", CabinetDeviceViewSet, basename="cabinet-device")
router.register(r"queue", AutomationQueueViewSet, basename="automation-queue")

urlpatterns = router.urls
