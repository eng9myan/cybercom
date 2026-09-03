# API & Event Contracts

Contract-first (ADR-0009). Nothing ships in the API without a contract here, reviewed by CDAC,
with consumer sign-off and contract tests in CI.

## Layout

```
contracts/
  openapi/
    core-v1.yaml            # canonical REST surface, OpenAPI 3.1 (generated from DRF + hand-augmented)
    onboarding-v1.yaml       # tenant onboarding / provisioning
    payments-v1.yaml         # carved payments service
    developer-portal-v1.yaml # public API surface + auth
  graphql/
    schema.graphql           # read/aggregation surface (persisted queries only in prod)
  asyncapi/
    events-v1.yaml           # domain event catalog (outbox → broker)
  webhooks/
    webhooks-v1.yaml         # outbound webhook payloads + signing
```

## Rules

1. **Versioning:** URL-major for REST (`/api/v1`, `/api/v2`). Two majors supported
   concurrently. Breaking change → new major + `Deprecation`/`Sunset` headers + ≥ 6-month
   window. Events: additive-only within a major; new required field = new major.
2. **Source of truth:** the YAML/GraphQL files here. Server code is generated from or
   validated against them in CI. Drift fails the build.
3. **Review:** any change to a file here is a CDAC-reviewed PR with the affected consumer
   pods tagged.
4. **Contract tests:** provider tests assert the implementation matches; consumer tests
   (Pact-style) assert expectations. Both gate the pipeline.
5. **Publish:** on merge, the developer portal + schema registry update automatically.

## Core APIs (spec bodies to be filled in Phase 0 — outlines in blueprint D.2)

| Contract | Endpoints (initial) |
|---|---|
| onboarding-v1 | `POST /onboarding/tenants`, `GET /onboarding/jobs/{id}` |
| core-v1 | `/catalog`, `/orders`, `/orders/{id}/checkout`, `/inventory/sync`, `/scheduling/appointments`, `/payroll/batches`, `/invoices`, `/finance/journals` |
| payments-v1 | `/payments`, `/payments/{id}/refund`, `/payments/webhooks/{provider}` |
| events-v1 | `tenant.*`, `catalog.*`, `order.*`, `inventory.*`, `finance.*`, `payment.*`, `hr.payroll.*`, `scheduling.*`, `clinical.*` |
