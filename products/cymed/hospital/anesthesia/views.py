from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.anesthesia.models import AnesthesiaAssessment, AnesthesiaPlan, AnesthesiaRecord, RecoveryAssessment
from products.cymed.hospital.anesthesia.serializers import (
    AnesthesiaAssessmentSerializer, AnesthesiaPlanSerializer, AnesthesiaRecordSerializer,
    RecoveryAssessmentSerializer
)

class AnesthesiaAssessmentViewSet(HospitalModelViewSet):
    queryset = AnesthesiaAssessment.objects.all()
    serializer_class = AnesthesiaAssessmentSerializer

class AnesthesiaPlanViewSet(HospitalModelViewSet):
    queryset = AnesthesiaPlan.objects.all()
    serializer_class = AnesthesiaPlanSerializer

class AnesthesiaRecordViewSet(HospitalModelViewSet):
    queryset = AnesthesiaRecord.objects.all()
    serializer_class = AnesthesiaRecordSerializer

class RecoveryAssessmentViewSet(HospitalModelViewSet):
    queryset = RecoveryAssessment.objects.all()
    serializer_class = RecoveryAssessmentSerializer
