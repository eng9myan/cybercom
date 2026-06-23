from rest_framework.routers import DefaultRouter
from .views import CultureViewSet, OrganismViewSet, SensitivityViewSet, ResistanceProfileViewSet, MicrobiologyResultViewSet

router = DefaultRouter()
router.register("cultures", CultureViewSet, basename="lab-cultures")
router.register("organisms", OrganismViewSet, basename="lab-organisms")
router.register("sensitivities", SensitivityViewSet, basename="lab-sensitivities")
router.register("resistance-profiles", ResistanceProfileViewSet, basename="lab-resistance-profiles")
router.register("microbiology-results", MicrobiologyResultViewSet, basename="lab-micro-results")

urlpatterns = router.urls
