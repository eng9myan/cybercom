from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.attendance.views import (
    AbsenceExplanationViewSet,
    AttendanceMarkViewSet,
    EmergencyDrillViewSet,
    LatePassViewSet,
    RollCallViewSet,
)

router = DefaultRouter()
router.register("roll-calls", RollCallViewSet)
router.register("marks", AttendanceMarkViewSet)
router.register("explanations", AbsenceExplanationViewSet)
router.register("emergency-drills", EmergencyDrillViewSet)
router.register("late-passes", LatePassViewSet)

urlpatterns = [path("", include(router.urls))]
