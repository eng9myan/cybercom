from rest_framework.routers import DefaultRouter

from .views import ImagingResultViewSet, ResultCommunicationViewSet, StructuredMeasurementViewSet

router = DefaultRouter()
router.register("results", ImagingResultViewSet, basename="imaging-result")
router.register("measurements", StructuredMeasurementViewSet, basename="structured-measurement")
router.register("communications", ResultCommunicationViewSet, basename="result-communication")

urlpatterns = router.urls
