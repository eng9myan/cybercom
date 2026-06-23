from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.discharge.models import DischargeChecklist, DischargeMedication, FollowUpAppointment, DischargeInstruction
from products.cymed.hospital.discharge.serializers import (
    DischargeChecklistSerializer, DischargeMedicationSerializer, FollowUpAppointmentSerializer,
    DischargeInstructionSerializer
)

class DischargeChecklistViewSet(HospitalModelViewSet):
    queryset = DischargeChecklist.objects.all()
    serializer_class = DischargeChecklistSerializer

class DischargeMedicationViewSet(HospitalModelViewSet):
    queryset = DischargeMedication.objects.all()
    serializer_class = DischargeMedicationSerializer

class FollowUpAppointmentViewSet(HospitalModelViewSet):
    queryset = FollowUpAppointment.objects.all()
    serializer_class = FollowUpAppointmentSerializer

class DischargeInstructionViewSet(HospitalModelViewSet):
    queryset = DischargeInstruction.objects.all()
    serializer_class = DischargeInstructionSerializer
