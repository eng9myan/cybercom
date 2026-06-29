from rest_framework.routers import DefaultRouter

from .views import (
    NationalHealthSnapshotViewSet,
    OutbreakForecastViewSet,
    PopulationAnalyticsInsightViewSet,
    PopulationHealthDashboardViewSet,
    QualityKPIDashboardViewSet,
)

router = DefaultRouter()
router.register("snapshots", NationalHealthSnapshotViewSet, basename="health-snapshot")
router.register("insights", PopulationAnalyticsInsightViewSet, basename="analytics-insight")
router.register("quality-kpis", QualityKPIDashboardViewSet, basename="quality-kpi")
router.register("outbreak-forecasts", OutbreakForecastViewSet, basename="outbreak-forecast")
router.register("dashboards", PopulationHealthDashboardViewSet, basename="ph-dashboard")

urlpatterns = router.urls
