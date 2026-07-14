from rest_framework.routers import DefaultRouter

from .views import (
    CensusDataPointViewSet,
    ForecastAdjustmentViewSet,
    ForecastRosterMappingViewSet,
    StaffingForecastViewSet,
)

router = DefaultRouter()
router.register("census-data", CensusDataPointViewSet, basename="census-data-point")
router.register("forecasts", StaffingForecastViewSet, basename="staffing-forecast")
router.register("adjustments", ForecastAdjustmentViewSet, basename="forecast-adjustment")
router.register("roster-mappings", ForecastRosterMappingViewSet, basename="forecast-roster-mapping")

urlpatterns = router.urls
