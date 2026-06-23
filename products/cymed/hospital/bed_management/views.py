from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.bed_management.models import BedAssignment, BedOccupancy, BedReservation, BedCleaning, BedMaintenance, BedBlocking
from products.cymed.hospital.bed_management.serializers import (
    BedAssignmentSerializer, BedOccupancySerializer, BedReservationSerializer,
    BedCleaningSerializer, BedMaintenanceSerializer, BedBlockingSerializer
)

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
