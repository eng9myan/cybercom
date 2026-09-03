"""
Prometheus metrics for the CyMed platform.

If ``prometheus_client`` is importable the real ``Counter`` / ``Histogram`` /
``Gauge`` classes are used and ``/metrics`` exposes the OpenMetrics text
format. When the dependency is missing, the module falls back to no-op stand-in
classes so import order stays predictable and application code does not need
guards of its own.

Metric names follow the ``cymed_*`` prefix and are stable across releases —
alerting rules can bind to them without version pinning.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

logger = logging.getLogger("cybercom.observability.metrics")

# ---------------------------------------------------------------------------
# Guarded import
# ---------------------------------------------------------------------------
try:
    from prometheus_client import (  # type: ignore
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover — fallback exercised via lint tests
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    class _NoOpMetric:
        """Silent stand-in for the real Prometheus metric classes."""

        def __init__(self, name: str, documentation: str = "", labelnames: Iterable[str] = ()) -> None:
            self.name = name
            self.documentation = documentation
            self.labelnames = tuple(labelnames)

        def labels(self, *args: Any, **kwargs: Any) -> "_NoOpMetric":
            return self

        def inc(self, amount: float = 1.0) -> None:  # noqa: D401
            return None

        def dec(self, amount: float = 1.0) -> None:  # noqa: D401
            return None

        def set(self, value: float) -> None:  # noqa: D401
            return None

        def observe(self, value: float) -> None:  # noqa: D401
            return None

        def time(self):  # noqa: D401
            class _Ctx:
                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, exc_type, exc, tb):
                    return None

            return _Ctx()

    class Counter(_NoOpMetric):  # type: ignore[no-redef]
        pass

    class Gauge(_NoOpMetric):  # type: ignore[no-redef]
        pass

    class Histogram(_NoOpMetric):  # type: ignore[no-redef]
        def __init__(
            self,
            name: str,
            documentation: str = "",
            labelnames: Iterable[str] = (),
            buckets: Iterable[float] = (),
        ) -> None:
            super().__init__(name, documentation, labelnames)
            self.buckets = tuple(buckets)

    def generate_latest(*_args: Any, **_kwargs: Any) -> bytes:  # type: ignore[no-redef]
        return b"# prometheus_client not installed -- install it to expose metrics.\n"


# ---------------------------------------------------------------------------
# HTTP request metrics — shared with AccessLogMiddleware
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "cymed_http_requests_total",
    "Total HTTP requests handled by the CyMed platform.",
    ["method", "path_tpl", "status", "tenant"],
)

REQUEST_LATENCY = Histogram(
    "cymed_http_request_seconds",
    "HTTP request duration in seconds.",
    ["method", "path_tpl"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_QUERY_COUNT = Counter(
    "cymed_db_queries_total",
    "Database queries executed per tenant.",
    ["tenant"],
)

# ---------------------------------------------------------------------------
# Domain metrics — billing, payments, clinical alerts
# ---------------------------------------------------------------------------
BILL_MINTED = Counter(
    "cymed_bill_minted_total",
    "Bills minted per tenant and currency.",
    ["tenant", "currency"],
)

PAYMENT_ATTEMPTED = Counter(
    "cymed_payment_attempted_total",
    "Payment attempts per tenant, gateway, and outcome.",
    ["tenant", "gateway", "status"],
)

PAYMENT_SUCCESS = Counter(
    "cymed_payment_success_total",
    "Successful payments per tenant and gateway.",
    ["tenant", "gateway"],
)

CDSS_ALERT_FIRED = Counter(
    "cymed_cds_alerts_total",
    "Clinical decision support alerts fired.",
    ["tenant", "kind", "severity"],
)

TRIAGE_CRITICAL_FIRED = Counter(
    "cymed_triage_critical_total",
    "Critical triage decisions surfaced.",
    ["tenant", "modality"],
)

ACTIVE_TENANTS = Gauge(
    "cymed_active_tenants",
    "Current tenants active in the last 24 hours.",
)


# ---------------------------------------------------------------------------
# Helper used by AccessLogMiddleware
# ---------------------------------------------------------------------------
def observe_request(
    *,
    method: str,
    path_tpl: str,
    status: int,
    tenant: str,
    duration_seconds: float,
) -> None:
    """Feed the HTTP request counter + latency histogram in one call."""
    try:
        REQUEST_COUNT.labels(
            method=method or "-",
            path_tpl=path_tpl or "-",
            status=str(status),
            tenant=tenant or "-",
        ).inc()
        REQUEST_LATENCY.labels(
            method=method or "-",
            path_tpl=path_tpl or "-",
        ).observe(float(duration_seconds))
    except Exception as exc:  # pragma: no cover
        logger.debug("metrics.observe_request_failed: %s", exc)


__all__ = [
    "PROMETHEUS_AVAILABLE",
    "CONTENT_TYPE_LATEST",
    "generate_latest",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "DB_QUERY_COUNT",
    "BILL_MINTED",
    "PAYMENT_ATTEMPTED",
    "PAYMENT_SUCCESS",
    "CDSS_ALERT_FIRED",
    "TRIAGE_CRITICAL_FIRED",
    "ACTIVE_TENANTS",
    "observe_request",
]
