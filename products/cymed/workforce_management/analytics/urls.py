from rest_framework.routers import DefaultRouter

from .views import OnCallSLAMetricViewSet, WorkforceAnalyticsSnapshotViewSet, WorkforceReportViewSet

router = DefaultRouter()
router.register(
    "snapshots", WorkforceAnalyticsSnapshotViewSet, basename="workforce-analytics-snapshot"
)
router.register("reports", WorkforceReportViewSet, basename="workforce-report")
router.register("oncall-sla", OnCallSLAMetricViewSet, basename="oncall-sla-metric")

urlpatterns = router.urls
