from rest_framework.routers import DefaultRouter
from .views import DICOMStudyViewSet, DICOMSeriesViewSet, DICOMInstanceViewSet, StudyArchiveViewSet

router = DefaultRouter()
router.register("studies", DICOMStudyViewSet, basename="dicom-study")
router.register("series", DICOMSeriesViewSet, basename="dicom-series")
router.register("instances", DICOMInstanceViewSet, basename="dicom-instance")
router.register("archives", StudyArchiveViewSet, basename="study-archive")

urlpatterns = router.urls
