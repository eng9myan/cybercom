from rest_framework.routers import DefaultRouter

from .views import MarketplaceOrderViewSet

router = DefaultRouter()
router.register("orders", MarketplaceOrderViewSet, basename="marketplace-order")

urlpatterns = router.urls
