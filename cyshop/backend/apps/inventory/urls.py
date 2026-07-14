from rest_framework.routers import DefaultRouter
from .views import (
    WarehouseViewSet, StockLocationViewSet, StockLevelViewSet,
    StockMovementViewSet, StockTransferViewSet,
)

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'locations', StockLocationViewSet, basename='stock-location')
router.register(r'levels', StockLevelViewSet, basename='stock-level')
router.register(r'movements', StockMovementViewSet, basename='stock-movement')
router.register(r'transfers', StockTransferViewSet, basename='stock-transfer')

urlpatterns = router.urls
