from products.cymed.clinic.clinical_forms.models import (
    ClinicalForm,
    ClinicalFormField,
    ClinicalFormSection,
    ClinicalFormSubmission,
    ClinicalFormTemplate,
)
from products.cymed.clinic.clinical_forms.serializers import (
    ClinicalFormFieldSerializer,
    ClinicalFormSectionSerializer,
    ClinicalFormSerializer,
    ClinicalFormSubmissionSerializer,
    ClinicalFormTemplateSerializer,
)
from products.cymed.clinic.views import ClinicModelViewSet


class ClinicalFormViewSet(ClinicModelViewSet):
    queryset = ClinicalForm.objects.all()
    serializer_class = ClinicalFormSerializer


class ClinicalFormSectionViewSet(ClinicModelViewSet):
    queryset = ClinicalFormSection.objects.all()
    serializer_class = ClinicalFormSectionSerializer


class ClinicalFormFieldViewSet(ClinicModelViewSet):
    queryset = ClinicalFormField.objects.all()
    serializer_class = ClinicalFormFieldSerializer


class ClinicalFormTemplateViewSet(ClinicModelViewSet):
    queryset = ClinicalFormTemplate.objects.all()
    serializer_class = ClinicalFormTemplateSerializer


class ClinicalFormSubmissionViewSet(ClinicModelViewSet):
    queryset = ClinicalFormSubmission.objects.all().order_by("-submitted_at")
    serializer_class = ClinicalFormSubmissionSerializer
