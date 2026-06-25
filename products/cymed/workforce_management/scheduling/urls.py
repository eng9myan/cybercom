from rest_framework.routers import DefaultRouter
from .views import (
    ShiftTemplateViewSet,
    RosterCycleViewSet,
    RosterSlotViewSet,
    SelfScheduleWindowViewSet,
    SlotQuotaViewSet,
)

router = DefaultRouter()
router.register("shift-templates", ShiftTemplateViewSet, basename="shift-template")
router.register("roster-cycles", RosterCycleViewSet, basename="roster-cycle")
router.register("roster-slots", RosterSlotViewSet, basename="roster-slot")
router.register("self-schedule-windows", SelfScheduleWindowViewSet, basename="self-schedule-window")
router.register("slot-quotas", SlotQuotaViewSet, basename="slot-quota")

urlpatterns = router.urls
