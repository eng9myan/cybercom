from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.hospital.nursing.views import (
    NursingShiftViewSet, NursingAssignmentViewSet, NursingAssessmentViewSet,
    NursingCarePlanViewSet, NursingTaskViewSet, NursingHandoverViewSet
)

router = DefaultRouter()
router.register("shifts", NursingShiftViewSet)
router.register("assignments", NursingAssignmentViewSet)
router.register("assessments", NursingAssessmentViewSet)
router.register("careplans", NursingCarePlanViewSet)
router.register("tasks", NursingTaskViewSet)
router.register("handovers", NursingHandoverViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
