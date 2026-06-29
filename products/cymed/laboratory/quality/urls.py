from rest_framework.routers import DefaultRouter

from .views import (
    ProficiencyTestViewSet,
    QualityControlViewSet,
    QualityFailureViewSet,
    QualityRuleViewSet,
    QualityRunViewSet,
)

router = DefaultRouter()
router.register("rules", QualityRuleViewSet, basename="lab-qc-rules")
router.register("controls", QualityControlViewSet, basename="lab-qc-controls")
router.register("runs", QualityRunViewSet, basename="lab-qc-runs")
router.register("failures", QualityFailureViewSet, basename="lab-qc-failures")
router.register("proficiency", ProficiencyTestViewSet, basename="lab-proficiency")

urlpatterns = router.urls
