from rest_framework.routers import DefaultRouter

from .views import (
    DisasterOverrideViewSet,
    DutyHourLogViewSet,
    FatigueViolationViewSet,
    WeeklyHoursSummaryViewSet,
)

router = DefaultRouter()
router.register("duty-logs", DutyHourLogViewSet, basename="duty-hour-log")
router.register("weekly-summaries", WeeklyHoursSummaryViewSet, basename="weekly-hours-summary")
router.register("violations", FatigueViolationViewSet, basename="fatigue-violation")
router.register("disaster-overrides", DisasterOverrideViewSet, basename="disaster-override")

urlpatterns = router.urls
