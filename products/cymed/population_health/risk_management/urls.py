from rest_framework.routers import DefaultRouter

from .views import (
    RiskAssessmentViewSet,
    RiskCategoryViewSet,
    RiskFactorViewSet,
    RiskScoreViewSet,
)

router = DefaultRouter()
router.register("scores", RiskScoreViewSet, basename="risk-scores")
router.register("factors", RiskFactorViewSet, basename="risk-factors")
router.register("categories", RiskCategoryViewSet, basename="risk-categories")
router.register("assessments", RiskAssessmentViewSet, basename="risk-assessments")

urlpatterns = router.urls
