# CyberCom Threat Model

Status: covers the products that actually exist as of Phase 9
(cymed, cyshop, cycom, cymart, cydrive, mobile, website, platform/shared).
STRIDE-style, scoped to real components, not a generic template.

## Assets

- Patient clinical data (`cymed` — hospital/clinic/laboratory/pharmacy/
  imaging). Highest sensitivity in the system.
- Payment tokens and settlement ledgers (`cymart.payments`,
  `cymart.settlement`) — no raw card data stored, but the ledgers
  themselves are financial records.
- CyIdentity credentials/sessions (`platform.cyidentity`) — compromise
  here cascades to every product that trusts it.
- Merchant/marketplace eligibility state (`cyshop.Company`/`Branch`,
  `cycom.res_company`/`pos_config`) — tampering could get an ineligible
  business onto CyMart.
- Delivery driver location/PII, cash-collection amounts (`cydrive`).

## Actors

- Authenticated end users (customers, merchants, drivers, clinicians) —
  via CyIdentity JWT.
- Service-to-service calls (cymart → cydrive job creation) — currently
  authenticated by forwarding the *calling user's* token, not a distinct
  service-account credential. **Real gap**: if a customer's token is used
  to call CyDrive on their behalf, CyDrive's authorization has to trust
  that cymart validated the request correctly — there's no independent
  service-identity check on the CyDrive side today.
- Unauthenticated/anonymous — blocked at `shared.auth.auth_middleware`
  except health checks and `/api/v1/public/*`.

## Threats and current mitigation status

**T1 — Cross-tenant data access.** Mitigated by `tenant_id` filtering
throughout, but enforcement is application-code, not database RLS (see
SECURITY_ARCHITECTURE.md). A missed `.filter(tenant_id=...)` in a new
endpoint is a real, not-yet-eliminated risk class — nothing in the
framework forces it.

**T2 — Marketplace eligibility bypass.** Mitigated — enforced in model
`clean()`/`save()` and Odoo `@api.constrains`, verified by tests that
specifically try to violate it (unsigned agreement, wrong status,
non-customer-facing company).

**T3 — Order/commission tampering.** Mitigated for the paths built: order
state machine rejects invalid transitions, commission calculations are an
immutable ledger (reversals are new rows, not mutations), idempotency
keys prevent duplicate order creation from a replayed webhook.

**T4 — CyDrive job spoofing.** Partially mitigated. `POST /fleet/jobs/`
requires a valid JWT but doesn't yet verify the caller is actually
authorized to create jobs for the specific `company` in the payload —
any authenticated user could currently attempt to create a job for any
`DeliveryCompany` id. Real gap, not caught by existing tests because the
tests use companies the test itself created. Needs a permission check
(caller must be staff of that company, or the request must carry a
verified service-to-service claim) before this is safe against a
malicious authenticated user.

**T5 — Payment provider compromise / no real PCI scope yet.** Not
applicable to the sandbox (there's no real money moving), but load-
bearing once a real `PaymentProvider` is wired in — see
SECURITY_ARCHITECTURE.md's payments section.

**T6 — AI prompt injection / PHI leakage via CyAI.** `GuardrailEngine`'s
regex-based PII/PHI scrubbing is real but narrow (email/phone/MRN
patterns only) — see `docs/ai/AI_AUDITABILITY.md`'s gap #3. Not exploitable
today since `ModelGateway` doesn't call a real model, but this is exactly
the kind of thing that has to be hardened *before*, not after, a real
provider goes live.

**T7 — Dependency vulnerabilities.** Addressed for Django (upgraded,
re-verified) this session. Not addressed for the shared Python
environment's other flagged packages — see SECURITY_ARCHITECTURE.md.

**T8 — Mobile token storage.** `react-native-keychain` with
`ACCESSIBLE.WHEN_UNLOCKED` + biometric gate for tokens — real code,
unverified on an actual device (no simulator in this environment).

## Highest-priority unresolved item

**T4** (CyDrive job authorization) is the most concrete, immediately
actionable gap found while writing this document — it's a real
authorization hole in code that exists and is deployed-shaped, not a
theoretical future risk like the payment/AI items. Recommended as the
first thing to fix in a follow-up pass.
