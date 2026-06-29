from rest_framework.routers import DefaultRouter

from .views import (
    HealthProgramViewSet,
    ProgramEnrollmentViewSet,
    ProgramMetricViewSet,
    ProgramOutcomeViewSet,
)

router = DefaultRouter()
router.register(r"programs", HealthProgramViewSet, basename="health-program")
router.register(r"enrollments", ProgramEnrollmentViewSet, basename="program-enrollment")
router.register(r"outcomes", ProgramOutcomeViewSet, basename="program-outcome")
router.register(r"metrics", ProgramMetricViewSet, basename="program-metric")

urlpatterns = router.urls
