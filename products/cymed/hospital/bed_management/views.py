from products.cymed.hospital.bed_management.models import (
    BedAssignment,
    BedBlocking,
    BedCleaning,
    BedMaintenance,
    BedOccupancy,
    BedReservation,
)
from products.cymed.hospital.bed_management.serializers import (
    BedAssignmentSerializer,
    BedBlockingSerializer,
    BedCleaningSerializer,
    BedMaintenanceSerializer,
    BedOccupancySerializer,
    BedReservationSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


class BedAssignmentViewSet(HospitalModelViewSet):
    queryset = BedAssignment.objects.all()
    serializer_class = BedAssignmentSerializer


class BedOccupancyViewSet(HospitalModelViewSet):
    queryset = BedOccupancy.objects.all()
    serializer_class = BedOccupancySerializer


class BedReservationViewSet(HospitalModelViewSet):
    queryset = BedReservation.objects.all()
    serializer_class = BedReservationSerializer


class BedCleaningViewSet(HospitalModelViewSet):
    queryset = BedCleaning.objects.all()
    serializer_class = BedCleaningSerializer


class BedMaintenanceViewSet(HospitalModelViewSet):
    queryset = BedMaintenance.objects.all()
    serializer_class = BedMaintenanceSerializer


class BedBlockingViewSet(HospitalModelViewSet):
    queryset = BedBlocking.objects.all()
    serializer_class = BedBlockingSerializer
