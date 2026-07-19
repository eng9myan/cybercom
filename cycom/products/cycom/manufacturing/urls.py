from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.manufacturing.views import (
    BillOfMaterialViewSet,
    BOMComponentViewSet,
    ManufacturingOrderViewSet,
)

router = DefaultRouter()
router.register("boms", BillOfMaterialViewSet)
router.register("bom-components", BOMComponentViewSet)
router.register("orders", ManufacturingOrderViewSet)

urlpatterns = [path("", include(router.urls))]
