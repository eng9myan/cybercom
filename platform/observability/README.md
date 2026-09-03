# platform.observability

Cross-cutting observability wiring for the CyMed platform: request-id
propagation, structured JSON logs, and Prometheus metrics.

## Modules

| Module | Purpose |
|---|---|
| `logging_config` | JSON `dictConfig` (structlog preferred, stdlib fallback). Every record carries `service`, `env`, `tenant_id`, `request_id`, `user_id` from contextvars. |
| `middleware.RequestIdMiddleware` | Reads / mints `X-Request-Id`; sets contextvars so all logs emitted in the request carry it. Echoes the id in the response header. |
| `middleware.AccessLogMiddleware` | One structured `http.access` record per request with `method / path / status / duration_ms / tenant_id / user_id / request_id / ip / user_agent`. Also feeds the Prometheus counters. |
| `metrics` | Counter / Histogram / Gauge definitions. Guarded import — no-op stand-ins when `prometheus_client` is absent. |
| `views.MetricsView` | HTTP handler at `/metrics` returning OpenMetrics text. |
| `urls` | URL config mounting the metrics view at `""`. |

## Wiring

```python
# core/settings.py
from platform.observability.logging_config import build_logging_config

LOGGING = build_logging_config(service="cymed", env=os.environ.get("PLATFORM_ENV", "dev"))

MIDDLEWARE = [
    "platform.observability.middleware.RequestIdMiddleware",
    "platform.observability.middleware.AccessLogMiddleware",
    "platform.security.middleware.SecurityHeadersMiddleware",
    "platform.security.middleware.ClientIntegrityMiddleware",
    "platform.security.middleware.RateLimitMiddleware",
    # ... existing middleware
]
```

```python
# core/urls.py
urlpatterns = [
    # ... health endpoints
    path("", include("platform.observability.urls")),  # exposes /metrics
]
```

## Metrics

| Metric | Type | Labels |
|---|---|---|
| `cymed_http_requests_total` | Counter | `method, path_tpl, status, tenant` |
| `cymed_http_request_seconds` | Histogram | `method, path_tpl` (buckets 0.01 … 5s) |
| `cymed_db_queries_total` | Counter | `tenant` |
| `cymed_bill_minted_total` | Counter | `tenant, currency` |
| `cymed_payment_attempted_total` | Counter | `tenant, gateway, status` |
| `cymed_payment_success_total` | Counter | `tenant, gateway` |
| `cymed_cds_alerts_total` | Counter | `tenant, kind, severity` |
| `cymed_triage_critical_total` | Counter | `tenant, modality` |
| `cymed_active_tenants` | Gauge | — |

## Prometheus scrape config

Add a job to your Prometheus config:

```yaml
scrape_configs:
  - job_name: cymed-platform
    metrics_path: /metrics
    scheme: https
    scrape_interval: 15s
    static_configs:
      - targets: ["cymed.internal:8000"]
        labels:
          service: cymed
          env: production
```

For dynamic environments prefer service discovery (Kubernetes, Consul, EC2)
rather than `static_configs`.

## Alert rules baseline

Save as `alerts/cymed.rules.yml` and load in Prometheus.

```yaml
groups:
  - name: cymed_platform
    interval: 30s
    rules:
      - alert: CymedHighLatency
        expr: |
          histogram_quantile(
            0.99,
            sum by (le, path_tpl) (rate(cymed_http_request_seconds_bucket[5m]))
          ) > 1
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "P99 latency > 1s on {{ $labels.path_tpl }}"

      - alert: CymedHigh5xxRate
        expr: |
          (
            sum(rate(cymed_http_requests_total{status=~"5.."}[5m]))
            /
            sum(rate(cymed_http_requests_total[5m]))
          ) > 0.01
        for: 10m
        labels: { severity: critical }
        annotations:
          summary: "5xx rate > 1% across the CyMed platform"

      - alert: CymedPaymentFailureRate
        expr: |
          (
            sum(rate(cymed_payment_attempted_total{status="failed"}[15m]))
            /
            sum(rate(cymed_payment_attempted_total[15m]))
          ) > 0.05
        for: 10m
        labels: { severity: critical }
        annotations:
          summary: "Payment failure rate > 5%"

      - alert: CymedDbQueryAnomaly
        expr: |
          (
            sum(rate(cymed_db_queries_total[5m]))
            /
            avg_over_time(sum(rate(cymed_db_queries_total[5m]))[1h:5m])
          ) > 3
        for: 15m
        labels: { severity: warning }
        annotations:
          summary: "DB query rate > 3x normal — possible N+1 regression"
```

## Grafana dashboard hints

* Request rate: `sum by (path_tpl) (rate(cymed_http_requests_total[5m]))`
* P50 / P95 / P99: `histogram_quantile(0.5|0.95|0.99, ...)` over
  `cymed_http_request_seconds_bucket`.
* Payment funnel: attempted vs. success per gateway.
* CDS pressure: alerts per severity, stacked.

## Log-vs-trace correlation

Every log record includes `request_id`. Propagate the same value into your
tracing layer (OTel `traceparent` from the same header, or copy `X-Request-Id`
as a span attribute) so a log entry maps to exactly one trace.
