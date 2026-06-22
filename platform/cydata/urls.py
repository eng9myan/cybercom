from django.urls import path, include
from rest_framework.routers import DefaultRouter
from platform.cydata.views import (
    DataAssetViewSet,
    DataLineageViewSet,
    DataQualityRuleViewSet,
    MasterDataMapViewSet,
    CDCPipelineLogViewSet
)

router = DefaultRouter()
router.register("assets", DataAssetViewSet, basename="data-asset")
router.register("lineage", DataLineageViewSet, basename="data-lineage")
router.register("quality-rules", DataQualityRuleViewSet, basename="data-quality-rule")
router.register("master-data", MasterDataMapViewSet, basename="master-data")
router.register("cdc-logs", CDCPipelineLogViewSet, basename="cdc-log")

urlpatterns = [
    path("", include(router.urls)),
]
