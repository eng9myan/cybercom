from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.transport.views import (
    BusLiveView,
    BusLocationViewSet,
    BusRouteViewSet,
    BusViewSet,
    CustomStopViewSet,
    RfidBoardingEventViewSet,
    RouteStopViewSet,
    TransportSubscriptionViewSet,
    TransportZoneViewSet,
)

router = DefaultRouter()
router.register("zones", TransportZoneViewSet)
router.register("buses", BusViewSet)
router.register("subscriptions", TransportSubscriptionViewSet)
router.register("custom-stops", CustomStopViewSet)
router.register("boarding-events", RfidBoardingEventViewSet)
router.register("routes", BusRouteViewSet)
router.register("route-stops", RouteStopViewSet)
router.register("locations", BusLocationViewSet)

urlpatterns = [
    path("buses/<uuid:bus_id>/live/", BusLiveView.as_view(), name="bus-live"),
    path("", include(router.urls)),
]
