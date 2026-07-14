from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.hospital.icu.views import (
    CriticalEventViewSet,
    ICUAssessmentViewSet,
    ICURoundViewSet,
    ICUStayViewSet,
    VentilatorRecordViewSet,
)

router = DefaultRouter()
router.register("stays", ICUStayViewSet)
router.register("rounds", ICURoundViewSet)
router.register("assessments", ICUAssessmentViewSet)
router.register("ventilators", VentilatorRecordViewSet)
router.register("critical-events", CriticalEventViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
