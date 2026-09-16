from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.attendance.views import (
    AbsenceExplanationViewSet,
    AttendanceMarkViewSet,
    EmergencyDrillViewSet,
    RollCallViewSet,
)

router = DefaultRouter()
router.register("roll-calls", RollCallViewSet)
router.register("marks", AttendanceMarkViewSet)
router.register("explanations", AbsenceExplanationViewSet)
router.register("emergency-drills", EmergencyDrillViewSet)

urlpatterns = [path("", include(router.urls))]
