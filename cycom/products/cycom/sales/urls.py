from rest_framework.routers import DefaultRouter

from products.cycom.sales.views import SalesOrderViewSet

router = DefaultRouter()
router.register("orders", SalesOrderViewSet, basename="sales-order")

urlpatterns = router.urls
