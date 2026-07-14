from products.cymed.clinic.specialties.models import (
    SpecialtyClinicalRule,
    SpecialtyProfile,
    SpecialtyQuestionnaire,
    SpecialtyTemplate,
)
from products.cymed.clinic.specialties.serializers import (
    SpecialtyClinicalRuleSerializer,
    SpecialtyProfileSerializer,
    SpecialtyQuestionnaireSerializer,
    SpecialtyTemplateSerializer,
)
from products.cymed.clinic.views import ClinicModelViewSet


class SpecialtyProfileViewSet(ClinicModelViewSet):
    queryset = SpecialtyProfile.objects.all()
    serializer_class = SpecialtyProfileSerializer


class SpecialtyTemplateViewSet(ClinicModelViewSet):
    queryset = SpecialtyTemplate.objects.all()
    serializer_class = SpecialtyTemplateSerializer


class SpecialtyQuestionnaireViewSet(ClinicModelViewSet):
    queryset = SpecialtyQuestionnaire.objects.all()
    serializer_class = SpecialtyQuestionnaireSerializer


class SpecialtyClinicalRuleViewSet(ClinicModelViewSet):
    queryset = SpecialtyClinicalRule.objects.all()
    serializer_class = SpecialtyClinicalRuleSerializer
