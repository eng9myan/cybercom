from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("warehouses", views.WarehouseViewSet, basename="warehouse")
router.register("stock-items", views.StockItemViewSet, basename="stock-item")
router.register("movements", views.StockMovementViewSet, basename="stock-movement")

urlpatterns = router.urls
