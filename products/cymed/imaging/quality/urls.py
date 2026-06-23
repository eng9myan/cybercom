from rest_framework.routers import DefaultRouter
from .views import QualityAuditViewSet, ImagingQualityMetricViewSet, RadiationDoseRecordViewSet, AccreditationRecordViewSet

router = DefaultRouter()
router.register("audits", QualityAuditViewSet, basename="quality-audit")
router.register("metrics", ImagingQualityMetricViewSet, basename="imaging-quality-metric")
router.register("dose-records", RadiationDoseRecordViewSet, basename="radiation-dose")
router.register("accreditation", AccreditationRecordViewSet, basename="accreditation")

urlpatterns = router.urls
