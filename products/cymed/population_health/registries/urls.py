from rest_framework.routers import DefaultRouter
from .views import (
    DiseaseRegistryViewSet,
    RegistryPatientViewSet,
    RegistryEnrollmentViewSet,
    RegistryStatusViewSet,
    RegistryOutcomeViewSet,
)

router = DefaultRouter()
router.register("disease-registries", DiseaseRegistryViewSet, basename="disease-registry")
router.register("registry-patients", RegistryPatientViewSet, basename="registry-patient")
router.register("registry-enrollments", RegistryEnrollmentViewSet, basename="registry-enrollment")
router.register("registry-status", RegistryStatusViewSet, basename="registry-status")
router.register("registry-outcomes", RegistryOutcomeViewSet, basename="registry-outcome")

urlpatterns = router.urls