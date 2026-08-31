from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.catalog.views import (
    CategoryViewSet,
    KitComponentViewSet,
    ProductUnitViewSet,
    ProductVariantViewSet,
    ProductViewSet,
    TaxClassViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("units", ProductUnitViewSet)
router.register("tax-classes", TaxClassViewSet)
router.register("products", ProductViewSet)
router.register("variants", ProductVariantViewSet)
router.register("kit-components", KitComponentViewSet)

urlpatterns = [path("", include(router.urls))]
