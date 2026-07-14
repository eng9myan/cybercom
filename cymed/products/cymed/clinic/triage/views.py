from products.cymed.clinic.triage.models import TriageAssessment, TriageRiskScore, TriageVitalSigns
from products.cymed.clinic.triage.serializers import (
    TriageAssessmentSerializer,
    TriageRiskScoreSerializer,
    TriageVitalSignsSerializer,
)
from products.cymed.clinic.views import ClinicModelViewSet


class TriageAssessmentViewSet(ClinicModelViewSet):
    queryset = TriageAssessment.objects.all()
    serializer_class = TriageAssessmentSerializer


class TriageVitalSignsViewSet(ClinicModelViewSet):
    queryset = TriageVitalSigns.objects.all()
    serializer_class = TriageVitalSignsSerializer


class TriageRiskScoreViewSet(ClinicModelViewSet):
    queryset = TriageRiskScore.objects.all()
    serializer_class = TriageRiskScoreSerializer
