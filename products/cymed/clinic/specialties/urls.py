from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.specialties.views import (
    SpecialtyProfileViewSet, SpecialtyTemplateViewSet, SpecialtyQuestionnaireViewSet, SpecialtyClinicalRuleViewSet
)

router = DefaultRouter()
router.register("profiles", SpecialtyProfileViewSet)
router.register("templates", SpecialtyTemplateViewSet)
router.register("questionnaires", SpecialtyQuestionnaireViewSet)
router.register("rules", SpecialtyClinicalRuleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
