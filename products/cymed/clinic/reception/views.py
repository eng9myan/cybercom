from products.cymed.clinic.views import ClinicModelViewSet
from products.cymed.clinic.reception.models import ArrivalMethod, VisitReason, VisitStatus, CheckIn, CheckOut, PatientQueueTicket
from products.cymed.clinic.reception.serializers import (
    ArrivalMethodSerializer, VisitReasonSerializer, VisitStatusSerializer,
    CheckInSerializer, CheckOutSerializer, PatientQueueTicketSerializer
)

class ArrivalMethodViewSet(ClinicModelViewSet):
    queryset = ArrivalMethod.objects.all()
    serializer_class = ArrivalMethodSerializer

class VisitReasonViewSet(ClinicModelViewSet):
    queryset = VisitReason.objects.all()
    serializer_class = VisitReasonSerializer

class VisitStatusViewSet(ClinicModelViewSet):
    queryset = VisitStatus.objects.all()
    serializer_class = VisitStatusSerializer

class CheckInViewSet(ClinicModelViewSet):
    queryset = CheckIn.objects.all()
    serializer_class = CheckInSerializer

class CheckOutViewSet(ClinicModelViewSet):
    queryset = CheckOut.objects.all()
    serializer_class = CheckOutSerializer

class PatientQueueTicketViewSet(ClinicModelViewSet):
    queryset = PatientQueueTicket.objects.all()
    serializer_class = PatientQueueTicketSerializer

