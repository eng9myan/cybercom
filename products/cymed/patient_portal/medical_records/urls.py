from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"access-log",
    views.MedicalRecordAccessViewSet,
    basename="portal-record-access",
)
router.register(
    r"shared",
    views.SharedRecordViewSet,
    basename="portal-shared-record",
)
router.register(
    r"download-history",
    views.RecordDownloadHistoryViewSet,
    basename="portal-download-history",
)
router.register(
    r"documents",
    views.PatientDocumentViewSet,
    basename="portal-patient-document",
)

urlpatterns = [path("", include(router.urls))]
