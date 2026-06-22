from products.cymed.clinic.views import ClinicModelViewSet
from products.cymed.clinic.triage.models import TriageAssessment, TriageVitalSigns, TriageRiskScore
from products.cymed.clinic.triage.serializers import (
    TriageAssessmentSerializer, TriageVitalSignsSerializer, TriageRiskScoreSerializer
)

class TriageAssessmentViewSet(ClinicModelViewSet):
    queryset = TriageAssessment.objects.all()
    serializer_class = TriageAssessmentSerializer

class TriageVitalSignsViewSet(ClinicModelViewSet):
    queryset = TriageVitalSigns.objects.all()
    serializer_class = TriageVitalSignsSerializer

class TriageRiskScoreViewSet(ClinicModelViewSet):
    queryset = TriageRiskScore.objects.all()
    serializer_class = TriageRiskScoreSerializer

