from products.cymed.hospital.views import HospitalModelViewSet
from products.cymed.hospital.operating_room.models import SurgicalCase, SurgicalSchedule, ProcedureBooking, ProcedureConsent, ProcedureChecklist, SurgicalTeam, SurgicalEquipment
from products.cymed.hospital.operating_room.serializers import (
    SurgicalCaseSerializer, SurgicalScheduleSerializer, ProcedureBookingSerializer,
    ProcedureConsentSerializer, ProcedureChecklistSerializer, SurgicalTeamSerializer,
    SurgicalEquipmentSerializer
)

class SurgicalCaseViewSet(HospitalModelViewSet):
    queryset = SurgicalCase.objects.all()
    serializer_class = SurgicalCaseSerializer

class SurgicalScheduleViewSet(HospitalModelViewSet):
    queryset = SurgicalSchedule.objects.all()
    serializer_class = SurgicalScheduleSerializer

class ProcedureBookingViewSet(HospitalModelViewSet):
    queryset = ProcedureBooking.objects.all()
    serializer_class = ProcedureBookingSerializer

class ProcedureConsentViewSet(HospitalModelViewSet):
    queryset = ProcedureConsent.objects.all()
    serializer_class = ProcedureConsentSerializer

class ProcedureChecklistViewSet(HospitalModelViewSet):
    queryset = ProcedureChecklist.objects.all()
    serializer_class = ProcedureChecklistSerializer

class SurgicalTeamViewSet(HospitalModelViewSet):
    queryset = SurgicalTeam.objects.all()
    serializer_class = SurgicalTeamSerializer

class SurgicalEquipmentViewSet(HospitalModelViewSet):
    queryset = SurgicalEquipment.objects.all()
    serializer_class = SurgicalEquipmentSerializer
