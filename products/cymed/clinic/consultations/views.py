from products.cymed.clinic.views import ClinicModelViewSet
from products.cymed.clinic.consultations.models import Consultation, ConsultationDiagnosis, ConsultationProcedure, ConsultationPlan, ConsultationFollowUp, ConsultationAttachment
from products.cymed.clinic.consultations.serializers import (
    ConsultationSerializer, ConsultationDiagnosisSerializer, ConsultationProcedureSerializer,
    ConsultationPlanSerializer, ConsultationFollowUpSerializer, ConsultationAttachmentSerializer
)

class ConsultationViewSet(ClinicModelViewSet):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer

class ConsultationDiagnosisViewSet(ClinicModelViewSet):
    queryset = ConsultationDiagnosis.objects.all()
    serializer_class = ConsultationDiagnosisSerializer

class ConsultationProcedureViewSet(ClinicModelViewSet):
    queryset = ConsultationProcedure.objects.all()
    serializer_class = ConsultationProcedureSerializer

class ConsultationPlanViewSet(ClinicModelViewSet):
    queryset = ConsultationPlan.objects.all()
    serializer_class = ConsultationPlanSerializer

class ConsultationFollowUpViewSet(ClinicModelViewSet):
    queryset = ConsultationFollowUp.objects.all()
    serializer_class = ConsultationFollowUpSerializer

class ConsultationAttachmentViewSet(ClinicModelViewSet):
    queryset = ConsultationAttachment.objects.all()
    serializer_class = ConsultationAttachmentSerializer

