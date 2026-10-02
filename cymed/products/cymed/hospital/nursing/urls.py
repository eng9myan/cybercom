from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.nursing.views import (
    MedicationAdministrationViewSet,
    NursingAssessmentViewSet,
    NursingAssignmentViewSet,
    NursingCarePlanViewSet,
    NursingHandoverViewSet,
    NursingShiftViewSet,
    NursingTaskViewSet,
)

router = DefaultRouter()
router.register("shifts", NursingShiftViewSet)
router.register("assignments", NursingAssignmentViewSet)
router.register("assessments", NursingAssessmentViewSet)
router.register("careplans", NursingCarePlanViewSet)
router.register("tasks", NursingTaskViewSet)
router.register("handovers", NursingHandoverViewSet)
router.register("mar", MedicationAdministrationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
