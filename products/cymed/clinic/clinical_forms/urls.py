from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.clinical_forms.views import (
    ClinicalFormViewSet, ClinicalFormSectionViewSet, ClinicalFormFieldViewSet,
    ClinicalFormTemplateViewSet, ClinicalFormSubmissionViewSet
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
