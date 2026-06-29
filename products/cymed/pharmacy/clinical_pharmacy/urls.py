"""Clinical Pharmacy URL routing."""

from rest_framework.routers import DefaultRouter

from .views import (
    ClinicalInterventionViewSet,
    MedicationReviewViewSet,
    MedicationTherapyManagementViewSet,
    PharmacistRecommendationViewSet,
)

router = DefaultRouter()
router.register(r"reviews", MedicationReviewViewSet, basename="medication-review")
router.register(r"interventions", ClinicalInterventionViewSet, basename="clinical-intervention")
router.register(
    r"recommendations", PharmacistRecommendationViewSet, basename="pharmacist-recommendation"
)
router.register(r"mtm", MedicationTherapyManagementViewSet, basename="medication-therapy-mgmt")

urlpatterns = router.urls
