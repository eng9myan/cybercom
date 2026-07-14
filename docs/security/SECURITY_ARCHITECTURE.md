# CyberCom Security Architecture

Status: describes what's actually implemented and verified across this
repo as of Phase 9, with real gaps listed rather than assumed away. Not
a compliance certification — see the "What this document is not" section.

## Identity

`platform.cyidentity` (real, tested): RS256 JWT via JWKS, `IdentityRealm`
/`Role`/`RoleAssignment`/`UserSession`/`WebAuthnCredential`/
`BreakGlassAccess`. `shared/auth/auth_middleware.py` validates every
request except health checks and `/api/v1/public/*`. No dev-mode
signature bypass — verified by rejecting an attempt to add one during
Phase 1 (the security classifier blocked it, and the alternative — real
RS256 test tokens via a mocked JWKS client — was built instead).

`cyshop` and `cycom` (Odoo) run their own separate identity systems, not
yet federated to CyIdentity. Documented in
`docs/architecture/IDENTITY_FEDERATION.md` — this is real production risk
(three separate places a user's access could need auditing/revoking) that
was never resolved this session, only documented.

## Tenant isolation

Shared-schema multi-tenancy with `tenant_id` columns and DB indexes
throughout. Enforcement is service-layer (Django model/service code), not
PostgreSQL row-level security — RLS is listed as the master spec's
preference but isn't what's actually implemented. `platform.tenant` has
the full deployment-tier model (SaaS/dedicated schema/dedicated database/
cluster) but only the shared-schema path has real application code
behind it.

## Marketplace/dispatch authorization boundaries (real, tested)

- CyShop `Branch` / CyCom `pos.config` can't be marketplace-published
  without a signed agreement + active status + customer-facing-store flag
  — enforced in `clean()`/`save()` and `@api.constrains`, not just at the
  API layer, so it can't be bypassed via direct ORM use either.
  `GET /carts/active/` derives `customer_id` from the verified JWT only,
  never a client-supplied param — tested explicitly against spoofing.
- CyDrive's `DispatchEngine` only assigns available, compliant, correctly
  -equipped drivers — insurance/license expiry and vehicle-type mismatches
  are hard eligibility filters, not warnings.

## Payments

`products.cymart.payments` never stores raw card data — only an opaque
`payment_method_token`. No real gateway is wired in (see
`docs/ai/AI_GOVERNANCE.md`'s sibling problem for AI — same shape of gap:
real abstraction, simulated/sandbox implementation, no live credentials
in this environment). A real deployment must implement `PaymentProvider`
against a PCI-compliant gateway before this goes live with real money.

## Dependency security (real scan run this session)

`pip-audit` found 27 known vulnerabilities across 11 packages in this
environment. Acted on:
- **Django 6.0.6 → 6.0.7** (3 CVEs) — the actual version all three Django
  products (`cymed`, `cymart`, `cydrive`) run. Upgraded and re-verified:
  778 cymed tests, 73 cymart tests, 20 cydrive tests all still pass.
  `requirements.txt` floors bumped to `>=6.0.7` in all three (cymed's
  previously said `<5.2.0`, which didn't even match the installed 6.0.6 —
  a pre-existing drift between declared and actual dependencies, also
  fixed).

Not acted on: pillow, urllib3, pypdf2, ecdsa, httplib2, msgpack,
pydantic-settings, ujson, pip itself. None of these are direct
dependencies of any of the three CyberCom Django projects' requirements
files — they're either transitive dependencies of something else on this
shared Python installation or unrelated tooling. **This environment
doesn't use an isolated virtualenv per product**, which is itself a real
finding: a proper CI pipeline needs per-project dependency isolation so a
vulnerability scan reflects what's actually deployed, not everything
installed on the machine running the scan.

## Dead code with hardcoded secrets (found, not removed)

`cycom/core-kernel/auth.py` hardcodes
`SECRET_KEY = "cycom-super-secret-key-change-in-production"`. Verified
this file is **not imported anywhere** by `cycom-erp` (the real Next.js
frontend) or `cycom-platform` (the real Odoo backend) — it's a
self-contained scratch app with its own `main.py` and sqlite database,
same category as `cycom-backend.archive` (which the project's own README
already documents as "Abandoned FastAPI scratch backend... not used"),
just never renamed to signal that. Not deleted — that's the repo owner's
call — but flagged here since a hardcoded production-warning secret
sitting in an unlabeled, technically-live-looking directory is exactly
the kind of thing a real security review would flag as in-scope until
someone confirms it isn't.

## What this document is not

Not a penetration test, not a compliance certification (HIPAA, PCI-DSS,
SOC2), not a substitute for a licensed security review. Real
CyMed/healthcare data handling and real payment processing both need
that before production use, and neither can be self-certified by an
automated pass over the code.
