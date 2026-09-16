from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.reporting.views import ReportCardEntryViewSet, ReportCardViewSet

router = DefaultRouter()
router.register("report-cards", ReportCardViewSet)
router.register("entries", ReportCardEntryViewSet)

urlpatterns = [path("", include(router.urls))]
