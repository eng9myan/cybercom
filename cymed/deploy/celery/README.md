# Celery worker + beat — run instructions

Runbook for the CyMed asynchronous execution tier. The web tier (Django /
DRF) must never block on outbound work that can be handed to Celery — invoice
stamping (ZATCA / JoFotara), NPHIES claim submission, notifications,
AI/CDS inference, and any retryable settlement operation belong on this tier.

---

## 1. Prerequisites

- **Redis 7+** reachable at the URLs referenced by:
  - `CELERY_BROKER_URL` (default `redis://localhost:6379/0`)
  - `CELERY_RESULT_BACKEND` (default `redis://localhost:6379/1`)
- Django settings loaded (`DJANGO_SETTINGS_MODULE=core.settings`).
- All `products/cymed/*` apps installed — worker autodiscovers `tasks.py`
  modules through `app.autodiscover_tasks()` in `core/celery.py`.

Environment variables consumed:

| Var | Default | Purpose |
|-----|---------|---------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | AMQP / Redis broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Task result store |
| `CELERY_TASK_TIME_LIMIT` | `300` | Hard time limit per task (seconds) |
| `DJANGO_SETTINGS_MODULE` | `core.settings` | Django settings entrypoint |

---

## 2. Local run (single host, all queues)

Start Redis first (`redis-server`), then from the CyMed repo root:

```
celery -A core worker -l INFO \
       -Q payments,integrations,notifications,ai_cds,default \
       -c 4
celery -A core beat -l INFO
```

`-A core` references `core/celery.py`; `-Q ...` binds this worker to the
listed queues; `-c 4` sets four worker processes (tune to CPU count).

Split workers per queue for isolation once the local system stabilises:

```
celery -A core worker -Q payments      -c 2 -n payments@%h        -l INFO
celery -A core worker -Q integrations  -c 4 -n integrations@%h    -l INFO
celery -A core worker -Q notifications -c 8 -n notifications@%h   -l INFO
celery -A core worker -Q ai_cds        -c 2 -n ai_cds@%h          -l INFO
celery -A core worker -Q default       -c 2 -n default@%h         -l INFO
```

---

## 3. Docker / Kubernetes

Production images live under `deploy/docker/` (build separately):

- `Dockerfile.worker` — same base as web image, entrypoint runs
  `celery -A core worker -Q <queue> -c <concurrency> -l INFO`
- `Dockerfile.beat` — schedules only; entrypoint `celery -A core beat -l INFO`
  and a **single** replica (never scale > 1).

Kubernetes manifests should:

- run beat as a `Deployment` with `replicas: 1` and a `PodDisruptionBudget`
  of `maxUnavailable: 0`,
- run each worker queue as its own `Deployment` scaled independently,
- expose Prometheus metrics via `celery-exporter` sidecar.

---

## 4. Queues — purpose and tuning

| Queue           | Routed via                       | Purpose                                                       | Tuning |
|-----------------|----------------------------------|---------------------------------------------------------------|--------|
| `payments`      | `payments.*`                     | ZATCA / JoFotara invoice stamping, settlement retries         | CPU-light, network-bound. Concurrency 2-4. Retry with backoff. |
| `integrations`  | `integrations.*`                 | NPHIES claim submission, eligibility, Hakeem bridge           | Network-bound. Concurrency 4-8. Long-running — raise soft time limit. |
| `notifications` | `notifications.*`                | SMS / WhatsApp / Email fan-out                                | High-throughput. Concurrency 8-16. Short tasks. |
| `ai_cds`        | `ai_cds.*`                       | AI clinical decision support inference                        | GPU / CPU-heavy. Concurrency 1-2 per worker; separate nodepool. |
| `default`       | catch-all                        | Anything unrouted                                             | Low concurrency (2). Investigate every task landing here. |

---

## 5. Retry & dead-letter policy

- **Default retry**: exponential backoff, `retry_backoff=True`,
  `retry_backoff_max=600`, `max_retries=5`, `retry_jitter=True`.
- **Non-retryable**: 4xx client errors from upstream regulators (ZATCA,
  NPHIES) — surface immediately, no auto-retry.
- **Retryable**: 5xx, timeouts, connection errors, rate-limit responses.
- **Dead-letter**: exhausted retries publish to `<queue>.dlq` (Redis list
  or Kafka topic per ADR-0004). The RCM ops dashboard must show DLQ depth
  per queue. Manual replay via `python manage.py celery_replay_dlq <queue>`.

Idempotency is a per-task requirement — see `docs/hardening/CELERY_TASKS.md`.

---

## 6. Monitoring

- **Flower** (dev / staging):
  `celery -A core flower --port=5555 --basic_auth=admin:$FLOWER_PASSWORD`
- **Prometheus + Grafana** (production): `celery-exporter` scraped by
  Prometheus; alerting on queue depth, task failure rate, worker liveness.
- **Sentry**: `CELERY_SEND_TASK_ERROR_EMAILS = False`; task failures
  automatically forwarded via the Sentry Celery integration configured in
  `platform/observability`.

Alert thresholds (starting values, tune after two sprints in production):

- `payments` queue depth > 100 for 5 min -> PagerDuty page
- `integrations` queue depth > 500 for 10 min -> Slack warning
- Any DLQ non-empty -> Slack warning; DLQ depth > 25 -> page
- Worker liveness < 1 replica per queue for 2 min -> page

---

## 7. Local troubleshooting

- `celery -A core inspect active` — running tasks per worker
- `celery -A core inspect reserved` — pre-fetched but not started
- `celery -A core purge -Q <queue>` — clear queue (DEV / STAGING ONLY)
- `redis-cli -n 0 LLEN celery` — raw broker depth on the default queue
