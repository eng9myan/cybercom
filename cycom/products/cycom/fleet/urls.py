from rest_framework.routers import DefaultRouter

from products.cycom.fleet.views import FuelLogViewSet, MaintenanceLogViewSet, VehicleViewSet

router = DefaultRouter()
router.register("vehicles", VehicleViewSet, basename="fleet-vehicle")
router.register("maintenance-logs", MaintenanceLogViewSet, basename="fleet-maintenance-log")
router.register("fuel-logs", FuelLogViewSet, basename="fleet-fuel-log")

urlpatterns = router.urls
