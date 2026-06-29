from rest_framework.routers import DefaultRouter

from .views import (
    CohortAnalysisViewSet,
    CohortMemberViewSet,
    CohortOutcomeViewSet,
    CohortViewSet,
)

router = DefaultRouter()
router.register("cohorts", CohortViewSet, basename="cohorts")
router.register("members", CohortMemberViewSet, basename="cohort-members")
router.register("outcomes", CohortOutcomeViewSet, basename="cohort-outcomes")
router.register("analyses", CohortAnalysisViewSet, basename="cohort-analyses")

urlpatterns = router.urls
