from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.curriculum.views import (
    AchievementStandardViewSet,
    CrossCurriculumPriorityViewSet,
    CurriculumOutcomeViewSet,
    GeneralCapabilityViewSet,
    MracImportRunViewSet,
)

router = DefaultRouter()
router.register("outcomes", CurriculumOutcomeViewSet)
router.register("general-capabilities", GeneralCapabilityViewSet, basename="general-capability")
router.register(
    "cross-curriculum-priorities", CrossCurriculumPriorityViewSet, basename="cross-curriculum-priority"
)
router.register("achievement-standards", AchievementStandardViewSet, basename="achievement-standard")
router.register("mrac-runs", MracImportRunViewSet, basename="mrac-run")

urlpatterns = [path("", include(router.urls))]
