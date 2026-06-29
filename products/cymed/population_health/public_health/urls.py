from rest_framework.routers import DefaultRouter

from .views import (
    FacilityAccreditationViewSet,
    HealthGoalViewSet,
    HealthRiskViewSet,
    NationalFacilityViewSet,
    NationalProviderViewSet,
    PopulationGroupViewSet,
    PopulationProgramViewSet,
    PopulationSegmentViewSet,
    ProviderCredentialViewSet,
)

router = DefaultRouter()
router.register("population-groups", PopulationGroupViewSet, basename="population-group")
router.register("population-segments", PopulationSegmentViewSet, basename="population-segment")
router.register("health-risks", HealthRiskViewSet, basename="health-risk")
router.register("health-goals", HealthGoalViewSet, basename="health-goal")
router.register("programs", PopulationProgramViewSet, basename="population-program")
router.register("national-providers", NationalProviderViewSet, basename="national-provider")
router.register("provider-credentials", ProviderCredentialViewSet, basename="provider-credential")
router.register("national-facilities", NationalFacilityViewSet, basename="national-facility")
router.register(
    "facility-accreditations", FacilityAccreditationViewSet, basename="facility-accreditation"
)

urlpatterns = router.urls
