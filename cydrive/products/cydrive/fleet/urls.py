from rest_framework.routers import DefaultRouter

from .views import DeliveryCompanyViewSet, DeliveryJobViewSet, DriverViewSet, VehicleViewSet

router = DefaultRouter()
router.register("companies", DeliveryCompanyViewSet, basename="delivery-company")
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("drivers", DriverViewSet, basename="driver")
router.register("jobs", DeliveryJobViewSet, basename="delivery-job")

urlpatterns = router.urls
