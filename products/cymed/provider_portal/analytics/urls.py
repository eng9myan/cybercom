from rest_framework.routers import DefaultRouter
from .views import (
    ProviderProductivitySnapshotViewSet,
    ClinicalQualityMetricViewSet,
    WorkforceDashboardSnapshotViewSet,
    ProviderAIInsightViewSet,
    ExecutiveDashboardMetricViewSet,
)

router = DefaultRouter()
router.register(
    r"productivity-snapshots",
    ProviderProductivitySnapshotViewSet,
    basename="productivity-snapshot",
)
router.register(
    r"quality-metrics",
    ClinicalQualityMetricViewSet,
    basename="quality-metric",
)
router.register(
    r"workforce-snapshots",
    WorkforceDashboardSnapshotViewSet,
    basename="workforce-snapshot",
)
router.register(
    r"ai-insights",
    ProviderAIInsightViewSet,
    basename="ai-insight",
)
router.register(
    r"executive-metrics",
    ExecutiveDashboardMetricViewSet,
    basename="executive-metric",
)

urlpatterns = router.urls
