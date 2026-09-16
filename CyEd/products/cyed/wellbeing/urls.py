from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.wellbeing.plan_views import (
    SupportAdjustmentViewSet,
    SupportGoalViewSet,
    SupportPlanViewSet,
)
from products.cyed.wellbeing.views import (
    BehaviourIncidentViewSet,
    LearnerProfileViewSet,
    WellbeingCheckInViewSet,
    WellbeingNoteViewSet,
)

router = DefaultRouter()
router.register("learner-profiles", LearnerProfileViewSet)
router.register("behaviour-incidents", BehaviourIncidentViewSet)
router.register("notes", WellbeingNoteViewSet)
router.register("checkins", WellbeingCheckInViewSet)
router.register("support-plans", SupportPlanViewSet)
router.register("support-adjustments", SupportAdjustmentViewSet)
router.register("support-goals", SupportGoalViewSet)

urlpatterns = [path("", include(router.urls))]
