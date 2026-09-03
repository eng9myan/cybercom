from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.plm.views import (
    BomComponentViewSet,
    EngineeringChangeOrderViewSet,
    ProductBOMViewSet,
)

router = DefaultRouter()
router.register("boms", ProductBOMViewSet)
router.register("bom-components", BomComponentViewSet)
router.register("ecos", EngineeringChangeOrderViewSet)

urlpatterns = [path("", include(router.urls))]
