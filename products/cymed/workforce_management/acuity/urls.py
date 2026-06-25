from rest_framework.routers import DefaultRouter
from .views import (
    PatientAcuityScoreViewSet,
    WardCoverageRequirementViewSet,
    CoverageValidationRunViewSet,
    SkillMixValidationViewSet,
)

router = DefaultRouter()
router.register("patient-scores", PatientAcuityScoreViewSet, basename="patient-acuity-score")
router.register("coverage-requirements", WardCoverageRequirementViewSet, basename="ward-coverage-req")
router.register("validation-runs", CoverageValidationRunViewSet, basename="coverage-validation-run")
router.register("skill-mix", SkillMixValidationViewSet, basename="skill-mix-validation")

urlpatterns = router.urls
