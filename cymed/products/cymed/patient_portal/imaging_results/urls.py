from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"results", views.ImagingResultViewViewSet, basename="imaging-result")
router.register(
    r"study-metadata",
    views.ImagingStudyMetadataViewSet,
    basename="imaging-study-metadata",
)
router.register(
    r"access-log",
    views.ImagingReportAccessViewSet,
    basename="imaging-report-access",
)
router.register(
    r"share-links",
    views.ImagingShareLinkViewSet,
    basename="imaging-share-link",
)

urlpatterns = [path("", include(router.urls))]
