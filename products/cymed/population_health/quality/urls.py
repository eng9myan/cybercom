from rest_framework.routers import DefaultRouter

from .views import (
    ClinicalAuditViewSet,
    QualityImprovementViewSet,
    QualityMeasureResultViewSet,
    QualityMeasureViewSet,
)

router = DefaultRouter()
router.register("measures", QualityMeasureViewSet, basename="quality-measures")
router.register("results", QualityMeasureResultViewSet, basename="quality-results")
router.register("improvements", QualityImprovementViewSet, basename="quality-improvements")
router.register("audits", ClinicalAuditViewSet, basename="clinical-audits")

urlpatterns = router.urls
