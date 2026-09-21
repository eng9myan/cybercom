from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.quality.views import (
    CheckpointCriterionResultViewSet,
    InspectionPlanViewSet,
    NonConformanceViewSet,
    QualityCheckpointViewSet,
)

router = DefaultRouter()
router.register("checkpoints", QualityCheckpointViewSet)
router.register("inspection-plans", InspectionPlanViewSet)
router.register("criterion-results", CheckpointCriterionResultViewSet)
router.register("non-conformances", NonConformanceViewSet)

urlpatterns = [path("", include(router.urls))]
