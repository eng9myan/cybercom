from rest_framework.routers import DefaultRouter

from .views import (
    AnalyzerInterfaceViewSet,
    AnalyzerMessageViewSet,
    AnalyzerResultViewSet,
    AnalyzerViewSet,
    LabWorklistViewSet,
    TechnologistAssignmentViewSet,
    WorklistItemViewSet,
)

router = DefaultRouter()
router.register("analyzers", AnalyzerViewSet, basename="lab-analyzers")
router.register("analyzer-interfaces", AnalyzerInterfaceViewSet, basename="lab-analyzer-interfaces")
router.register("analyzer-messages", AnalyzerMessageViewSet, basename="lab-analyzer-messages")
router.register("analyzer-results", AnalyzerResultViewSet, basename="lab-analyzer-results")
router.register("worklists", LabWorklistViewSet, basename="lab-worklists")
router.register("worklist-items", WorklistItemViewSet, basename="lab-worklist-items")
router.register(
    "technologist-assignments", TechnologistAssignmentViewSet, basename="lab-tech-assignments"
)

urlpatterns = router.urls
