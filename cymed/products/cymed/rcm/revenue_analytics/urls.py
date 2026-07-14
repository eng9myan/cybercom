from rest_framework.routers import DefaultRouter

from .views import (
    ClaimMetricsSnapshotViewSet,
    DenialAnalyticsSnapshotViewSet,
    PayerPerformanceSnapshotViewSet,
    RCMAIInsightViewSet,
    RevenueDashboardSnapshotViewSet,
    RevenueLeakageAlertViewSet,
)

router = DefaultRouter()
router.register(r"revenue-snapshots", RevenueDashboardSnapshotViewSet, basename="revenue-snapshot")
router.register(r"claim-metrics", ClaimMetricsSnapshotViewSet, basename="claim-metrics")
router.register(r"denial-analytics", DenialAnalyticsSnapshotViewSet, basename="denial-analytics")
router.register(r"payer-performance", PayerPerformanceSnapshotViewSet, basename="payer-performance")
router.register(r"ai-insights", RCMAIInsightViewSet, basename="ai-insight")
router.register(r"leakage-alerts", RevenueLeakageAlertViewSet, basename="leakage-alert")

urlpatterns = router.urls
