from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.inventory.views import InventoryItemViewSet, StockMoveViewSet

router = DefaultRouter()
router.register("items", InventoryItemViewSet)
router.register("moves", StockMoveViewSet)

urlpatterns = [path("", include(router.urls))]
