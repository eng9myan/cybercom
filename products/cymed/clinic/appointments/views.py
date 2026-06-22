from products.cymed.clinic.views import ClinicModelViewSet
from products.cymed.clinic.appointments.models import ClinicAppointment, AppointmentReminder, AppointmentWaitlist, AppointmentTemplate, AppointmentRule
from products.cymed.clinic.appointments.serializers import (
    ClinicAppointmentSerializer, AppointmentReminderSerializer,
    AppointmentWaitlistSerializer, AppointmentTemplateSerializer, AppointmentRuleSerializer
)

class ClinicAppointmentViewSet(ClinicModelViewSet):
    queryset = ClinicAppointment.objects.all()
    serializer_class = ClinicAppointmentSerializer

class AppointmentReminderViewSet(ClinicModelViewSet):
    queryset = AppointmentReminder.objects.all()
    serializer_class = AppointmentReminderSerializer

class AppointmentWaitlistViewSet(ClinicModelViewSet):
    queryset = AppointmentWaitlist.objects.all().order_by("-priority")
    serializer_class = AppointmentWaitlistSerializer

class AppointmentTemplateViewSet(ClinicModelViewSet):
    queryset = AppointmentTemplate.objects.all()
    serializer_class = AppointmentTemplateSerializer

class AppointmentRuleViewSet(ClinicModelViewSet):
    queryset = AppointmentRule.objects.all()
    serializer_class = AppointmentRuleSerializer

