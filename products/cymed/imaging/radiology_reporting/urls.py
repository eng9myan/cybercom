from rest_framework.routers import DefaultRouter

from .views import (
    CriticalFindingViewSet,
    RadiologyFindingViewSet,
    RadiologyImpressionViewSet,
    RadiologyReportViewSet,
    ReportAmendmentViewSet,
    ReportTemplateViewSet,
    StructuredReportViewSet,
)

router = DefaultRouter()
router.register("templates", ReportTemplateViewSet, basename="report-template")
router.register("reports", RadiologyReportViewSet, basename="radiology-report")
router.register("findings", RadiologyFindingViewSet, basename="radiology-finding")
router.register("impressions", RadiologyImpressionViewSet, basename="radiology-impression")
router.register("critical-findings", CriticalFindingViewSet, basename="critical-finding")
router.register("structured-reports", StructuredReportViewSet, basename="structured-report")
router.register("amendments", ReportAmendmentViewSet, basename="report-amendment")

urlpatterns = router.urls
