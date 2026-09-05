from rest_framework.routers import DefaultRouter

from .views import CarrierViewSet, DeliveryOrderViewSet, RouteViewSet, ShipmentViewSet

router = DefaultRouter()
router.register("carriers", CarrierViewSet, basename="logistics-carrier")
router.register("shipments", ShipmentViewSet, basename="logistics-shipment")
router.register("delivery-orders", DeliveryOrderViewSet, basename="logistics-delivery-order")
router.register("routes", RouteViewSet, basename="logistics-route")

urlpatterns = router.urls
