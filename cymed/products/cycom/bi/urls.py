from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("reports", views.BIReportViewSet, basename="bi-report")
router.register("metrics", views.DashboardMetricViewSet, basename="bi-metric")

urlpatterns = router.urls
