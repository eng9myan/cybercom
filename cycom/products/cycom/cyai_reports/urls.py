from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.cyai_reports.views import (
    ReportBuilderSessionViewSet,
    ReportDefinitionViewSet,
    ReportScheduleViewSet,
)

router = DefaultRouter()
router.register("sessions", ReportBuilderSessionViewSet)
router.register("reports", ReportDefinitionViewSet)
router.register("schedules", ReportScheduleViewSet)

urlpatterns = [path("", include(router.urls))]
