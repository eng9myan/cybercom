from rest_framework.routers import DefaultRouter
from .views import (
    OnCallRosterViewSet,
    OnCallAssignmentViewSet,
    OnCallPageViewSet,
    OnCallEscalationViewSet,
    CallSwapRequestViewSet,
)

router = DefaultRouter()
router.register("rosters", OnCallRosterViewSet, basename="oncall-roster")
router.register("assignments", OnCallAssignmentViewSet, basename="oncall-assignment")
router.register("pages", OnCallPageViewSet, basename="oncall-page")
router.register("escalations", OnCallEscalationViewSet, basename="oncall-escalation")
router.register("call-swaps", CallSwapRequestViewSet, basename="call-swap-request")

urlpatterns = router.urls
