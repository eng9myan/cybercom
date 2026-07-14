from products.cymed.clinic.consultations.models import (
    Consultation,
    ConsultationAttachment,
    ConsultationDiagnosis,
    ConsultationFollowUp,
    ConsultationPlan,
    ConsultationProcedure,
)
from products.cymed.clinic.consultations.serializers import (
    ConsultationAttachmentSerializer,
    ConsultationDiagnosisSerializer,
    ConsultationFollowUpSerializer,
    ConsultationPlanSerializer,
    ConsultationProcedureSerializer,
    ConsultationSerializer,
)
from products.cymed.clinic.views import ClinicModelViewSet


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
