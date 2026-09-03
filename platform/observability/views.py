"""
HTTP endpoints for the observability app.

``MetricsView`` exposes the Prometheus scrape endpoint at ``/metrics`` (mounted
via :mod:`platform.observability.urls`). The response is the standard
``text/plain; version=0.0.4`` OpenMetrics format, or an explanatory placeholder
when the ``prometheus_client`` dependency is missing.
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.views import View

from platform.observability.metrics import CONTENT_TYPE_LATEST, generate_latest


class MetricsView(View):
    """Prometheus scrape endpoint."""

    http_method_names = ["get", "head"]

    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
