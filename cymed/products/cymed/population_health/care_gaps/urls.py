from rest_framework.routers import DefaultRouter

from .views import (
    CareGapRecommendationViewSet,
    CareGapResolutionViewSet,
    CareGapRuleViewSet,
    CareGapViewSet,
)

router = DefaultRouter()
router.register("gaps", CareGapViewSet, basename="care-gaps")
router.register("rules", CareGapRuleViewSet, basename="care-gap-rules")
router.register(
    "recommendations", CareGapRecommendationViewSet, basename="care-gap-recommendations"
)
router.register("resolutions", CareGapResolutionViewSet, basename="care-gap-resolutions")

urlpatterns = router.urls
