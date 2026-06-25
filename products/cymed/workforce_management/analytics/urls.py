from rest_framework.routers import DefaultRouter
from .views import WorkforceAnalyticsSnapshotViewSet, WorkforceReportViewSet, OnCallSLAMetricViewSet

router = DefaultRouter()
router.register("snapshots", WorkforceAnalyticsSnapshotViewSet, basename="workforce-analytics-snapshot")
router.register("reports", WorkforceReportViewSet, basename="workforce-report")
router.register("oncall-sla", OnCallSLAMetricViewSet, basename="oncall-sla-metric")

urlpatterns = router.urls
