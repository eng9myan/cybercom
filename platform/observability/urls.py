"""URL config for the observability app — exposes ``/metrics``."""

from django.urls import path

from platform.observability.views import MetricsView

urlpatterns = [
    path("metrics", MetricsView.as_view(), name="metrics"),
]
