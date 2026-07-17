from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.inventory.views import (
    InternalOrderLineViewSet,
    InternalOrderViewSet,
    ProductViewSet,
    StockItemViewSet,
    StockMoveViewSet,
    WarehouseViewSet,
)

router = DefaultRouter()
router.register("warehouses", WarehouseViewSet)
router.register("products", ProductViewSet)
router.register("stock-items", StockItemViewSet)
router.register("moves", StockMoveViewSet)
router.register("internal-orders", InternalOrderViewSet)
router.register("internal-order-lines", InternalOrderLineViewSet)

urlpatterns = [path("", include(router.urls))]
