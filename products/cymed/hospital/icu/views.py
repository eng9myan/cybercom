from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.icu.models import ICUStay, ICURound, ICUAssessment, VentilatorRecord, CriticalEvent
from products.cymed.hospital.icu.serializers import (
    ICUStaySerializer, ICURoundSerializer, ICUAssessmentSerializer,
    VentilatorRecordSerializer, CriticalEventSerializer
)

class ICUStayViewSet(HospitalModelViewSet):
    queryset = ICUStay.objects.all()
    serializer_class = ICUStaySerializer

class ICURoundViewSet(HospitalModelViewSet):
    queryset = ICURound.objects.all()
    serializer_class = ICURoundSerializer

class ICUAssessmentViewSet(HospitalModelViewSet):
    queryset = ICUAssessment.objects.all()
    serializer_class = ICUAssessmentSerializer

class VentilatorRecordViewSet(HospitalModelViewSet):
    queryset = VentilatorRecord.objects.all()
    serializer_class = VentilatorRecordSerializer

class CriticalEventViewSet(HospitalModelViewSet):
    queryset = CriticalEvent.objects.all()
    serializer_class = CriticalEventSerializer
