from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.provider_portal.patient_lists.views import (
    PatientAssignmentViewSet,
    PatientCensusViewSet,
    PatientListViewSet,
    ProviderAssignmentViewSet,
)

router = DefaultRouter()
router.register(r"lists", PatientListViewSet, basename="patient-list")
router.register(r"assignments", PatientAssignmentViewSet, basename="patient-assignment")
router.register(r"provider-assignments", ProviderAssignmentViewSet, basename="provider-assignment")
router.register(r"census", PatientCensusViewSet, basename="patient-census")

urlpatterns = [
    path("", include(router.urls)),
]
