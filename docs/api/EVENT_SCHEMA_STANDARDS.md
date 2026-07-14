# CyberCom Event Schema Standards

Status: describes what `platform/events/` actually implements, verified
against code as of the Phase 1 platform promotion. Not aspirational.

## Transport

Transactional outbox pattern. `OutboxEvent` rows are written atomically with
the business record in the same DB transaction; Debezium (documented, not
verified running in this environment) tails the PostgreSQL WAL via CDC and
publishes to Kafka through `KafkaEventPublisher`
(`platform/events/publisher.py`), which wraps `confluent-kafka` with
`acks=all`, `enable.idempotence=True`, snappy compression. If
`confluent-kafka` isn't installed, publishing is disabled with a warning
rather than raising — event writes to the outbox table still succeed.

## OutboxEvent schema (actual model fields)

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `tenant_id` | UUID | indexed |
| `topic` | string(500) | indexed — see topic registry below |
| `event_type` | string(200) | indexed — see schema registry below |
| `payload` | JSON | event body |
| `headers` | JSON | free-form, default `{}` |
| `status` | enum | `pending` / `published` / `failed` |
| `created_at` | datetime | indexed |
| `published_at` | datetime | nullable |
| `error_message` | text | |
| `retry_count` | int | |

**Gap, verified against the model, not assumed:** there are no first-class
`correlation_id`, `causation_id`, or `trace_id` columns, and no
`schema_version` field. The master spec calls for all four. Today they'd
have to be stuffed into the free-form `headers` JSON with no enforced
convention — meaning nothing guarantees two producers use the same header
key. Needs a migration adding these as real columns before they can be
relied on platform-wide. Not fixed here — flagging per "stop and document
blockers rather than inventing missing business rules."

## Topic registry (`platform/events/registry.py`)

```
cyidentity → platform.identity.events
tenant     → platform.tenant.events
audit      → platform.audit.events
api        → platform.api.gateway.events
cymed      → product.cymed.clinical.events
cycom      → product.cycom.erp.events
cyshop     → product.cyshop.retail.events
cygov      → product.cygov.governance.events
cyconnect  → product.cyconnect.comms.events
cycitizen  → product.cycitizen.citizen.events
cydata     → platform.cydata.lakehouse.events
cyai       → platform.cyai.inference.events
```

No `cymart` or `cydrive` topics exist yet — added when those products exist
(Phase 3 / Phase 5).

## Event type registry (`EVENT_SCHEMAS`)

10 event types are currently registered with a required-field list each
(e.g. `cyidentity.user.provisioned`, `tenant.provisioned`,
`cymed.patient.admission`, `cymed.prescription.written`). `EventRegistry.
validate_event()` checks a payload's keys against this list before
publishing. This is a field-presence check, not a JSON Schema / Avro
contract — no type validation, no versioning of the schema itself. Extend
`EVENT_SCHEMAS` when adding new event types; don't publish an unregistered
`event_type` without adding it here first, or `validate_event` won't catch
malformed payloads.

The master spec's canonical event list (`marketplace.order_created`,
`payment.captured`, `delivery.driver_assigned`, `settlement.generated`,
etc.) doesn't exist yet — those products don't exist yet either (Phases 3,
5, 7).

## Signing

`platform/events/signing.py` — `EventSigner`. HMAC-SHA256 over
`f"{tenant_id}:" + payload_bytes`, keyed by `settings.JWT_SIGNING_KEY`
(falls back to a hardcoded dev key if unset — **same class of gap as the
auth middleware's dev path; don't deploy with `JWT_SIGNING_KEY` unset**).
The module docstring says production should use an RSA key from Vault; the
actual implementation is HMAC only. Verify before trusting signature
verification as a cross-tenant integrity guarantee in production.

## Replay

`platform/events/replay.py` — `EventReplayManager.replay_events(tenant_id,
topic, start_time=None, end_time=None, event_types=None)`. Re-publishes
matching `OutboxEvent` rows through `KafkaEventPublisher`, tagging replayed
messages with `x-replay: true` and `x-original-created-at` headers so
consumers can distinguish replays from live events.

## Dead-letter handling

`DeadLetterEvent` and `EventDeliveryLog` models exist (`platform/events/
models.py`) for tracking failed deliveries, but this audit didn't trace the
full retry → DLQ transition logic end-to-end — flagged for the next pass
rather than described without verification.
