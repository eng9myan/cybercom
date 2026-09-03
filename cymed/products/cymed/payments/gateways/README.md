# CyMed payment gateways

Router-model integrations. **Card data never touches CyMed servers** — the
front-end talks to the vendor's hosted fields (COPYandPay for HyperPay,
Stripe Elements for Stripe) and only opaque tokens / checkout ids cross our
API boundary. That keeps CyMed on the **SAQ-A** PCI scope.

## Gateways

| Gateway    | Module            | Scope    | Sandbox host                |
|------------|-------------------|----------|-----------------------------|
| HyperPay   | `hyperpay.py`     | KSA/GCC  | `https://eu-test.oppwa.com` |
| Stripe     | `stripe_gw.py`    | Global   | (Stripe test keys)          |

## HyperPay

### Environment variables

| Variable                  | Required | Default                      | Notes |
|---------------------------|----------|------------------------------|-------|
| `HYPERPAY_BASE_URL`       | no       | `https://eu-test.oppwa.com`  | Prod: `https://eu-prod.oppwa.com` (or your merchant's region) |
| `HYPERPAY_ACCESS_TOKEN`   | yes      | —                            | OAuth bearer token from HyperPay |
| `HYPERPAY_ENTITY_ID`      | yes      | —                            | Channel/entity id — one per brand/currency |
| `HYPERPAY_WEBHOOK_SECRET` | yes      | —                            | Shared secret for HMAC-SHA256 body verification |

Never hard-code these. Use `.env` in dev, secrets manager in prod.

### Endpoints used

| Verb   | Path                                     | Purpose                       |
|--------|------------------------------------------|-------------------------------|
| POST   | `/v1/checkouts`                          | Create hosted checkout session |
| GET    | `/v1/checkouts/{id}/payment`             | Poll checkout status          |
| POST   | `/v1/registrations`                      | Tokenise a card (server-to-server; sandbox only) |
| POST   | `/v1/registrations/{token}/payments`     | Charge a saved token (paymentType=DB) |
| POST   | `/v1/payments/{transaction_id}`          | Refund (paymentType=RF)       |

### HTTP behaviour

- `httpx.Client` with explicit **30 s** timeout and `Authorization: Bearer …`.
- `httpx.HTTPTransport(retries=2)` — retries **network errors only**, never
  a completed 4xx/5xx response.
- 4xx/5xx bubbles up via `response.raise_for_status()`. No silent excepts.
- Every request/response is structured-logged via
  `logging.getLogger("cymed.payments.hyperpay")` — never PAN, never token
  material, only ids and metadata.

### Idempotency & multi-tenant

`charge()` and `refund()` accept keyword-only `idempotency_key=` (also sent
as `merchantTransactionId` and `Idempotency-Key` header) and `charge()`
accepts `tenant_id=` (stamped as `customParameters[tenantId]` so webhooks
can be routed back to the originating tenant).

### Webhooks

`webhook_verify(headers, raw_body)` recomputes
`HMAC-SHA256(HYPERPAY_WEBHOOK_SECRET, raw_body)` and compares to the
`X-Signature` header with `hmac.compare_digest`. Always pass the **raw
untransformed request body** — parsing JSON first will corrupt the digest.

## Stripe

Standard `stripe` SDK — see `stripe_gw.py`. Environment:

| Variable                | Required |
|-------------------------|----------|
| `STRIPE_API_KEY`        | yes      |
| `STRIPE_WEBHOOK_SECRET` | yes      |

The `stripe` pip package is **optional**; import happens lazily.

## PCI DSS SAQ scope

CyMed operates as a **payment router**, not a cardholder-data processor:

1. Card entry happens in the vendor's hosted iframe / SDK on the merchant's
   own domain.
2. Only the resulting **token** (registration id / payment method id) or
   **checkout id** ever hits CyMed servers.
3. CyMed **never** stores, processes, or transmits raw PAN, CVV, or full
   track data.

That places CyMed on **SAQ-A**. The moment we accept a raw PAN on any of
our surfaces — even in a debug endpoint — scope escalates to SAQ-A-EP or
SAQ-D. The server-to-server `tokenize()` helper in `hyperpay.py` is
sandbox-only for that reason: **do not** wire it to a production endpoint.

## Before going live checklist

- [ ] Vendor account fully KYC-verified; production credentials issued.
- [ ] `HYPERPAY_BASE_URL` flipped to the production origin.
- [ ] Secrets moved out of `.env` files into the secrets manager
      (Vault / AWS Secrets Manager / Azure Key Vault).
- [ ] Webhook endpoint reachable from vendor IP ranges, TLS 1.2+, valid
      cert, no self-signed.
- [ ] Webhook signature verification confirmed with a signed test event.
- [ ] `idempotency_key` wired through the whole charge path so retries
      never double-bill.
- [ ] All logs scanned for PAN / CVV leakage; log shipper redacts anyway.
- [ ] Structured log correlation id includes `tenant_id` on every payment
      log line.
- [ ] Refund and partial-refund happy paths tested against sandbox with
      matching amounts.
- [ ] 3DS challenge flow exercised end-to-end.
- [ ] Rate limit + circuit-breaker in front of the gateway so a HyperPay
      outage does not cascade to CyMed.
- [ ] Load test: sustained charge throughput matches expected pilot volume.
- [ ] Disaster-recovery drill: revoke and rotate `HYPERPAY_ACCESS_TOKEN`
      and confirm rollout in under an hour.
- [ ] Confirmed PCI SAQ-A eligibility with the QSA / acquirer in writing.
- [ ] Runbook published: how to reconcile a stuck payment, how to trigger
      a manual refund, who to page on gateway 5xx spikes.
- [ ] On-call alerts wired to the `cymed.payments.hyperpay` logger for
      `ERROR` level and for elevated 4xx rates.

## Dependencies

- `httpx>=0.27,<1.0` — HTTP client (already in `requirements.txt`).
- `stripe` — optional, install only if the Stripe gateway is used.
