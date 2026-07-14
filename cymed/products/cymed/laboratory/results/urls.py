from rest_framework.routers import DefaultRouter

from .views import (
    CriticalResultViewSet,
    LabResultViewSet,
    ReferenceRangeViewSet,
    ResultApprovalViewSet,
    ResultCorrectionViewSet,
    ResultValueViewSet,
)

router = DefaultRouter()
router.register("results", LabResultViewSet, basename="lab-results")
router.register("result-values", ResultValueViewSet, basename="lab-result-values")
router.register("reference-ranges", ReferenceRangeViewSet, basename="lab-reference-ranges")
router.register("critical-results", CriticalResultViewSet, basename="lab-critical-results")
router.register("corrections", ResultCorrectionViewSet, basename="lab-corrections")
router.register("approvals", ResultApprovalViewSet, basename="lab-approvals")

urlpatterns = router.urls
