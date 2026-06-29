from products.cymed.hospital.emergency.models import (
    EmergencyAcuity,
    EmergencyDisposition,
    EmergencyObservation,
    EmergencyTracking,
    EmergencyTriage,
    EmergencyVisit,
)
from products.cymed.hospital.emergency.serializers import (
    EmergencyAcuitySerializer,
    EmergencyDispositionSerializer,
    EmergencyObservationSerializer,
    EmergencyTrackingSerializer,
    EmergencyTriageSerializer,
    EmergencyVisitSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


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
