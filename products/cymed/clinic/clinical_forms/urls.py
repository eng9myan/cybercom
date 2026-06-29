from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.clinical_forms.views import (
    ClinicalFormFieldViewSet,
    ClinicalFormSectionViewSet,
    ClinicalFormSubmissionViewSet,
    ClinicalFormTemplateViewSet,
    ClinicalFormViewSet,
)

router = DefaultRouter()
router.register("forms", ClinicalFormViewSet)
router.register("sections", ClinicalFormSectionViewSet)
router.register("fields", ClinicalFormFieldViewSet)
router.register("templates", ClinicalFormTemplateViewSet)
router.register("submissions", ClinicalFormSubmissionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
