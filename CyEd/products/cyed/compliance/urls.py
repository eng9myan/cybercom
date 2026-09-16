from django.urls import path
from rest_framework.routers import DefaultRouter

from products.cyed.compliance.views import (
    AttendanceReturnView, CensusView, NaplanParticipationView, NCCDRecordViewSet,
    NCCDReturnView, NCCDSummaryView, StatutoryReportLogViewSet,
)

router = DefaultRouter()
router.register("nccd-records", NCCDRecordViewSet, basename="nccd-record")
router.register("report-logs", StatutoryReportLogViewSet, basename="statutory-report-log")

urlpatterns = [
    path("exports/nccd/", NCCDReturnView.as_view(), name="export-nccd"),
    path("exports/nccd-summary/", NCCDSummaryView.as_view(), name="export-nccd-summary"),
    path("exports/attendance/", AttendanceReturnView.as_view(), name="export-attendance"),
    path("exports/naplan/", NaplanParticipationView.as_view(), name="export-naplan"),
    path("exports/census/", CensusView.as_view(), name="export-census"),
]
urlpatterns += router.urls
