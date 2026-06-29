from django.urls import path

from platform.common.views import platform_dashboard_metrics

urlpatterns = [
    path("dashboard-metrics/", platform_dashboard_metrics, name="platform-dashboard-metrics"),
]
