from products.cymed.hospital.discharge.models import (
    DischargeChecklist,
    DischargeInstruction,
    DischargeMedication,
    FollowUpAppointment,
)
from products.cymed.hospital.discharge.serializers import (
    DischargeChecklistSerializer,
    DischargeInstructionSerializer,
    DischargeMedicationSerializer,
    FollowUpAppointmentSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


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
