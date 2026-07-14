from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.core.scheduling.views import AppointmentViewSet, ScheduleSlotViewSet

router = DefaultRouter()
router.register(r"slots", ScheduleSlotViewSet, basename="schedule-slot")
router.register(r"", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
]
