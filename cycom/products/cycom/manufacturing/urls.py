from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.manufacturing.views import (
    BillOfMaterialViewSet,
    BOMComponentViewSet,
    ManufacturingOrderViewSet,
    RoutingViewSet,
    WorkCenterViewSet,
    WorkOrderViewSet,
)

router = DefaultRouter()
router.register("boms", BillOfMaterialViewSet)
router.register("bom-components", BOMComponentViewSet)
router.register("work-centers", WorkCenterViewSet)
router.register("routings", RoutingViewSet)
router.register("work-orders", WorkOrderViewSet)
router.register("orders", ManufacturingOrderViewSet)

urlpatterns = [path("", include(router.urls))]
