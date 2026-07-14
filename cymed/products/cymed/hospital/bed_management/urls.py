from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.bed_management.views import (
    BedAssignmentViewSet,
    BedBlockingViewSet,
    BedCleaningViewSet,
    BedMaintenanceViewSet,
    BedOccupancyViewSet,
    BedReservationViewSet,
)

router = DefaultRouter()
router.register("assignments", BedAssignmentViewSet)
router.register("occupancy", BedOccupancyViewSet)
router.register("reservations", BedReservationViewSet)
router.register("cleaning", BedCleaningViewSet)
router.register("maintenance", BedMaintenanceViewSet)
router.register("blocking", BedBlockingViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
