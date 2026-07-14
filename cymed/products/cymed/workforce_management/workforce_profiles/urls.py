from rest_framework.routers import DefaultRouter

from .views import ClinicalCredentialViewSet, CompetencyRecordViewSet, WorkforceProfileViewSet

router = DefaultRouter()
router.register("profiles", WorkforceProfileViewSet, basename="workforce-profile")
router.register("credentials", ClinicalCredentialViewSet, basename="clinical-credential")
router.register("competencies", CompetencyRecordViewSet, basename="competency-record")

urlpatterns = router.urls
