from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.reporting.views import SavedReportViewSet, report_sources_meta

router = DefaultRouter()
router.register("saved-reports", SavedReportViewSet)

urlpatterns = [
    path("sources/", report_sources_meta, name="reporting-sources-meta"),
    path("", include(router.urls)),
]
