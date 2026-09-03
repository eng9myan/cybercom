# Celery task contract — CyMed async tier

This document is the source of truth for every named Celery task shipped by
CyMed. Every task listed here is registered under an explicit name in
`CELERY_TASK_ROUTES` (`core/settings.py`) so the queue router lands it on the
correct worker pool. Tasks marked **wired but not implemented** raise
`NotImplementedError` on purpose — the wiring exists so callers can enqueue
against a stable name before the implementation lands, and the router keeps
the load off the wrong queue.

See `deploy/celery/README.md` for the operational side (worker layout, retry
policy, dead-letter handling, monitoring).

---

## Global conventions

- **Naming**: `<domain>.<action>` — matches the router glob (`payments.*`,
  `integrations.*`, `notifications.*`, `ai_cds.*`). Anything else lands on
  the `default` queue and is a bug.
- **Serialization**: JSON only. Never pickle. Pass identifiers (UUIDs,
  primary keys) not Django model instances.
- **Idempotency**: every task takes a natural key (bill_id, txn_id, claim
  correlation id) and MUST NOT double-side-effect when re-run. The retry
  path re-invokes with the same arguments.
- **Retry policy**: `retry_backoff=True`, `max_retries=5`,
  `retry_jitter=True`. Transient (5xx, network, timeout, throttle) auto-retry;
  permanent (4xx, validation) do NOT retry — surface to caller and DLQ.
- **Observability**: every task logs `task_id`, natural key, upstream
  correlation id, latency, outcome. Errors ship to Sentry via
  `platform.observability`.

---

## Queue: `payments` — routed via `payments.*`

### `payments.stamp_bill_zatca(bill_id: str) -> str`

- **Purpose**: submit a paid `UnifiedBill` to ZATCA (Saudi e-invoicing),
  persist `zatca_qr` and `zatca_uuid` on the bill, and return the ZATCA UUID.
- **Inputs**: `bill_id` — UUID of `UnifiedBill`.
- **Side effects**: updates `UnifiedBill.zatca_qr`, `UnifiedBill.zatca_uuid`,
  `UnifiedBill.updated_at`. Emits `payments.bill.zatca_stamped` domain event.
- **Idempotency**: `UnifiedBill.zatca_uuid` acts as a fingerprint — task
  MUST short-circuit if already set.
- **Retry**: 5xx / timeout / throttle -> retry. Validation failure -> DLQ,
  emit `payments.bill.zatca_failed`.
- **Status**: wired but not implemented.

### `payments.stamp_bill_jofotara(bill_id: str) -> str`

- **Purpose**: submit a paid `UnifiedBill` to JoFotara (Jordan e-invoicing),
  persist `jofotara_qr` and `jofotara_uuid`, and return the JoFotara UUID.
- **Inputs**: `bill_id` — UUID of `UnifiedBill`.
- **Side effects**: updates `UnifiedBill.jofotara_qr`,
  `UnifiedBill.jofotara_uuid`, `UnifiedBill.updated_at`. Emits
  `payments.bill.jofotara_stamped`.
- **Idempotency**: guarded by `UnifiedBill.jofotara_uuid` presence.
- **Retry**: same policy as `stamp_bill_zatca`.
- **Status**: wired but not implemented.

### `payments.retry_failed_settlement(txn_id: str) -> str`

- **Purpose**: re-attempt a settlement / payout transaction that previously
  landed in a failed terminal state due to a transient upstream error.
- **Inputs**: `txn_id` — UUID of the settlement transaction row.
- **Side effects**: updates the transaction's status, gateway reference,
  and attempt counter. Emits `payments.settlement.retried`.
- **Idempotency**: the transaction row's `attempt_counter` and
  `gateway_idempotency_key` prevent double-charge on retry.
- **Retry**: bounded to 3 additional attempts; further failure -> DLQ +
  ops alert.
- **Status**: wired but not implemented.

---

## Queue: `integrations` — routed via `integrations.*`

### `integrations.nphies_submit_claim(claim_payload: dict) -> str`

- **Purpose**: submit an FHIR Claim resource bundle to NPHIES (Saudi
  insurance clearinghouse) asynchronously.
- **Inputs**: `claim_payload` — JSON-serialisable dict containing a FHIR R4
  Claim bundle plus a caller-supplied `correlation_id`.
- **Side effects**: writes NPHIES message log row; on success updates the
  originating Claim row with the NPHIES reference id; emits
  `integrations.nphies.claim_submitted`.
- **Idempotency**: `correlation_id` used as the NPHIES `MessageHeader.id` —
  duplicate submits are safe (NPHIES rejects the second with a
  known-duplicate response, which is treated as success).
- **Retry**: 5xx / timeout / throttle -> retry. Validation (`OperationOutcome`
  severity=error) -> DLQ.
- **Status**: wired but not implemented.

### `integrations.nphies_check_eligibility_async(payload: dict) -> str`

- **Purpose**: fire-and-forget CoverageEligibilityRequest against NPHIES;
  outcome delivered via webhook (`platform.cyintegrationhub`) rather than
  return value.
- **Inputs**: `payload` — dict containing patient membership number, service
  date, provider, and correlation id.
- **Side effects**: NPHIES eligibility log row; webhook fan-out on
  response; emits `integrations.nphies.eligibility_checked`.
- **Idempotency**: guarded by `correlation_id`; re-runs re-emit the webhook
  (webhook consumers must be idempotent, per ADR-0004).
- **Retry**: standard; DLQ on validation error.
- **Status**: wired but not implemented.

---

## Queue: `notifications` — routed via `notifications.*`

All three notification tasks share the same contract: enqueue-and-forget,
delivery receipt handled asynchronously by the transport provider's webhook
(`platform.cyintegrationhub`). Return value is the provider message id.

### `notifications.send_sms(to: str, body: str) -> str`

- **Purpose**: send a transactional SMS.
- **Inputs**: `to` — E.164-formatted MSISDN. `body` — plain text, <= 640
  characters (multi-part SMS handled by the transport).
- **Side effects**: writes `platform.notifications.OutboundMessage` row;
  emits `notifications.sms.sent`.
- **Idempotency**: caller supplies `Idempotency-Key` header equivalent via
  a per-task `client_reference` kwarg (added in the implementation ticket).
- **Retry**: standard. Permanent bad-number errors -> DLQ.
- **Status**: wired but not implemented.

### `notifications.send_whatsapp(to: str, body: str) -> str`

- **Purpose**: send a WhatsApp Business API message using a pre-approved
  template.
- **Inputs**: `to` — E.164 MSISDN. `body` — either a template variable
  payload or free text (24-hour session window rules apply and are enforced
  at the transport layer).
- **Side effects**: `platform.notifications.OutboundMessage` row; emits
  `notifications.whatsapp.sent`.
- **Idempotency**: same `client_reference` pattern as SMS.
- **Retry**: standard. Template-mismatch / opt-out -> DLQ.
- **Status**: wired but not implemented.

### `notifications.send_email(to: str, subject: str, html: str) -> str`

- **Purpose**: send a transactional email (patient receipts, appointment
  confirmations, insurance EOBs).
- **Inputs**: `to` — RFC 5321 address. `subject`. `html` — pre-rendered
  HTML body; plain-text alternative auto-generated by the transport.
- **Side effects**: `platform.notifications.OutboundMessage` row; emits
  `notifications.email.sent`.
- **Idempotency**: `client_reference` pattern.
- **Retry**: standard. Hard bounce -> DLQ + suppress list.
- **Status**: wired but not implemented.

---

## Rollout checklist per task

When a task graduates from "wired" to implemented:

1. Replace the `raise NotImplementedError` body with the real client call.
2. Add unit tests covering happy path, retryable failure, permanent
   failure, idempotency re-run.
3. Add an integration test that enqueues via `.delay()` in a Redis-backed
   test worker (`pytest-celery`).
4. Move the entry in this document from **wired but not implemented** to
   **live** and record the go-live date.
5. Wire the queue-depth and failure-rate alerts in Grafana.
6. Update `deploy/celery/README.md` if the queue's concurrency / tuning
   guidance changes.
