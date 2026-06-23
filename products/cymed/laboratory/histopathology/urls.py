from rest_framework.routers import DefaultRouter
from .views import HistologyCaseViewSet, TissueBlockViewSet, SlideViewSet, SlideReviewViewSet, HistologyDiagnosisViewSet

router = DefaultRouter()
router.register("histology-cases", HistologyCaseViewSet, basename="lab-histo-cases")
router.register("tissue-blocks", TissueBlockViewSet, basename="lab-tissue-blocks")
router.register("slides", SlideViewSet, basename="lab-slides")
router.register("slide-reviews", SlideReviewViewSet, basename="lab-slide-reviews")
router.register("histology-diagnoses", HistologyDiagnosisViewSet, basename="lab-histo-diagnoses")

urlpatterns = router.urls
