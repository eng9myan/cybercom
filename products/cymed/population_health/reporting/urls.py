from rest_framework.routers import DefaultRouter
from .views import (
    NationalReportViewSet,
    ReportTemplateViewSet,
    GovernmentSubmissionViewSet,
    ReportScheduleViewSet,
)

router = DefaultRouter()
router.register("national-reports", NationalReportViewSet, basename="national-report")
router.register("templates", ReportTemplateViewSet, basename="report-template")
router.register("submissions", GovernmentSubmissionViewSet, basename="gov-submission")
router.register("schedules", ReportScheduleViewSet, basename="report-schedule")

urlpatterns = router.urls
