from rest_framework.routers import DefaultRouter

from .views import (
    LabMicrobiologyDashboardViewSet,
    LabOperationsDashboardViewSet,
    LabProductivityReportViewSet,
    LabQualityDashboardViewSet,
    LabTurnaroundMetricViewSet,
)

router = DefaultRouter()
router.register("ops-dashboard", LabOperationsDashboardViewSet, basename="lab-ops-dashboard")
router.register("tat-metrics", LabTurnaroundMetricViewSet, basename="lab-tat-metrics")
router.register("productivity", LabProductivityReportViewSet, basename="lab-productivity")
router.register("quality-dashboard", LabQualityDashboardViewSet, basename="lab-quality-dashboard")
router.register(
    "microbiology-dashboard", LabMicrobiologyDashboardViewSet, basename="lab-micro-dashboard"
)

urlpatterns = router.urls
