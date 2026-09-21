from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.appointments.views import (
    AppointmentTypeViewSet,
    AvailabilitySlotViewSet,
    BookingViewSet,
    ResourceViewSet,
)

router = DefaultRouter()
router.register("types", AppointmentTypeViewSet)
router.register("resources", ResourceViewSet)
router.register("availability-slots", AvailabilitySlotViewSet)
router.register("bookings", BookingViewSet)

urlpatterns = [path("", include(router.urls))]
