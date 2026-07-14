from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.clinic.specialties.views import (
    SpecialtyClinicalRuleViewSet,
    SpecialtyProfileViewSet,
    SpecialtyQuestionnaireViewSet,
    SpecialtyTemplateViewSet,
)

router = DefaultRouter()
router.register("profiles", SpecialtyProfileViewSet)
router.register("templates", SpecialtyTemplateViewSet)
router.register("questionnaires", SpecialtyQuestionnaireViewSet)
router.register("rules", SpecialtyClinicalRuleViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
