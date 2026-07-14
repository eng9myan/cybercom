from products.cymed.hospital.operating_room.models import (
    ProcedureBooking,
    ProcedureChecklist,
    ProcedureConsent,
    SurgicalCase,
    SurgicalEquipment,
    SurgicalSchedule,
    SurgicalTeam,
)
from products.cymed.hospital.operating_room.serializers import (
    ProcedureBookingSerializer,
    ProcedureChecklistSerializer,
    ProcedureConsentSerializer,
    SurgicalCaseSerializer,
    SurgicalEquipmentSerializer,
    SurgicalScheduleSerializer,
    SurgicalTeamSerializer,
)
from products.cymed.hospital.views import HospitalModelViewSet


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
