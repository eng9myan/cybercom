from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.hospital.bed_management.views import (
    BedAssignmentViewSet, BedOccupancyViewSet, BedReservationViewSet,
    BedCleaningViewSet, BedMaintenanceViewSet, BedBlockingViewSet
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
