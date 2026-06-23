from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.emergency.models import EmergencyVisit, EmergencyTriage, EmergencyAcuity, EmergencyDisposition, EmergencyObservation, EmergencyTracking
from products.cymed.hospital.emergency.serializers import (
    EmergencyVisitSerializer, EmergencyTriageSerializer, EmergencyAcuitySerializer,
    EmergencyDispositionSerializer, EmergencyObservationSerializer, EmergencyTrackingSerializer
)

class EmergencyVisitViewSet(HospitalModelViewSet):
    queryset = EmergencyVisit.objects.all()
    serializer_class = EmergencyVisitSerializer

class EmergencyTriageViewSet(HospitalModelViewSet):
    queryset = EmergencyTriage.objects.all()
    serializer_class = EmergencyTriageSerializer

class EmergencyAcuityViewSet(HospitalModelViewSet):
    queryset = EmergencyAcuity.objects.all()
    serializer_class = EmergencyAcuitySerializer

class EmergencyDispositionViewSet(HospitalModelViewSet):
    queryset = EmergencyDisposition.objects.all()
    serializer_class = EmergencyDispositionSerializer

class EmergencyObservationViewSet(HospitalModelViewSet):
    queryset = EmergencyObservation.objects.all()
    serializer_class = EmergencyObservationSerializer

class EmergencyTrackingViewSet(HospitalModelViewSet):
    queryset = EmergencyTracking.objects.all()
    serializer_class = EmergencyTrackingSerializer
