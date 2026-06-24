from rest_framework.routers import DefaultRouter
from .views import (
    EpidemiologyStudyViewSet,
    DiseaseTrendViewSet,
    PopulationIndicatorViewSet,
    HealthMeasureViewSet,
)

router = DefaultRouter()
router.register(r"studies", EpidemiologyStudyViewSet, basename="epidemiology-study")
router.register(r"disease-trends", DiseaseTrendViewSet, basename="disease-trend")
router.register(r"population-indicators", PopulationIndicatorViewSet, basename="population-indicator")
router.register(r"health-measures", HealthMeasureViewSet, basename="health-measure")

urlpatterns = router.urls
