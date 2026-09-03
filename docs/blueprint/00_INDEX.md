# CyberCom Unified ERP Ecosystem — Blueprint Package

> **Objective:** merge CyShop + CyCom + CyMed into a single multi-tenant, API-first,
> flavor-templated ERP ecosystem — Gulf-first, zero-trust, cloud-native.
> **Author:** engineering (blueprint pass). **Date:** 2026-09-04. **Status:** draft for founder/architecture-council review.
> Grounded in a direct source audit of `D:\Cybercom launch\cybercom` on 2026-09-04, not aspiration.

---

## How to read this package

| Doc | Section | Purpose | Primary audience |
|---|---|---|---|
| `00_INDEX.md` | I + baseline | This file: catalog, current-state truth, artifact list | everyone |
| `A_executive_synthesis.md` | A | One-page strategic objective + the "why now / why this shape" | founder, investors, stakeholders |
| `B_market_gap_analysis.md` | B | Competitor complaints, differentiators to own, where we must outperform | product strategy, investors |
| `C_architecture_blueprint.md` | C | Canonical cloud-native architecture, flavor model, service map, component + deployment diagrams | architects, platform team |
| `D_data_model_apis_migration.md` | D | Canonical entities/ERD, core API contracts, 3-schema→1 migration playbook | backend, data, integration owners |
| `E_vertical_flavor_mvps.md` | E | 4 flavor MVP blueprints (Retail, Health, AutoParts, Grocery) + cross-domain workflows | product, delivery pods |
| `F_governance_security_compliance.md` | F | Architecture council charter, security controls, Gulf regulatory map (PDPL, ZATCA, PCI, NPHIES) | governance, security, legal |
| `G_rollout_12_18_months.md` | G | Phase 0–7 milestone chart with gating criteria | founder, delivery leads |
| `H_nfr_checklist.md` | H | Non-functional requirements with testable thresholds | SRE, QA, architects |
| `J_constraints_gates.md` | J | Locked assumptions + go/no-go decision gates | founder, architecture council |
| `K_90day_sprint.md` | K | Week-by-week 90-day quick-start | delivery leads |
| `L_partner_ecosystem_plan.md` | L (extra) | Payments/delivery/gov/health partner integrations, order + commercials | founder, integrations |
| `M_risk_register.md` | M (extra) | Living risk register, scored, owned | everyone |

Read order for a first pass: **A → B → C → E → G → K**. Deep dives: D, F, H, J, L, M.

## Phase 0 scaffolding shipped alongside this package

| Path | What |
|---|---|
| `docs/adr/` | ADR process + `TEMPLATE.md` + index (14 ADRs); 0001–0003 written (canonical core, modular monolith, flavor-is-config); 0004–0014 pre-stated for CDAC to ratify |
| `docs/blueprint/templates/RFC_TEMPLATE.md` | RFC format for CDAC |
| `docs/blueprint/schemas/flavor.schema.yaml` | machine-enforceable flavor definition schema + `examples/retail.flavor.yaml` |
| `docs/blueprint/contracts/README.md` | contract-first repo layout (OpenAPI/GraphQL/AsyncAPI/webhooks) + rules |

---

## Baseline — checkout reconciliation (R01) — DONE 2026-09-04

A source audit on 2026-09-04 found the codebase split across three locations. Reconciled the same day:

| Location | Was | Now |
|---|---|---|
| `D:\cybercom` | `feat/oci-demo-deploy` @ `0e90866`, ~135 files uncommitted (incl. whole untracked app trees: CyMed integrations, portals, RCM, FHIR, `platform/security`, `platform/observability`, CyCom gap-fill apps) | **CANONICAL.** ~760 files committed as `7848b40` (pre-consolidation baseline); this blueprint committed on top; `develop` fast-forwarded here; pushed to `origin/develop`. |
| `D:\Cybercom launch\cybercom` | full monorepo, `develop` @ `9060c9d`, ~195 files uncommitted, this package authored here | superseded — treat read-only, do not edit. Anything unique still here (audit docs) to be cherry-picked if needed. |
| `D:\Cybercom launch\Cybercom-launch` | 1-commit "CyShop-first" scaffold | superseded by this unified plan — archive/delete. |

**Origin:** `github.com/eng9myan/cybercom.git`. After reconciliation, `origin/develop` carries the full buildout + this blueprint.

**Excluded from the baseline commit** (see `.gitignore`): ruflo/claude local state, `*.db`, the local dev Keycloak realm (dev seed password), and `/CyEd/` — pending scope decision **J.2 O5**.

---

## Current-state inventory (audited 2026-09-04)

Stack (verified): **Django + DRF** backend · **Next.js 16 (App Router, TS)** frontend · **PostgreSQL** prod / **SQLite** dev · **Keycloak OIDC** prod + `dev-auth` fake-JWT shim · shared `platform/` Django apps.

| Product | Backend apps | ~Py LOC (excl. migrations) | Test files | Frontend | Maturity |
|---|---|---|---|---|---|
| **CyCom** — general ERP flagship | 39 (`cycom/products/cycom/`) | ~15k | 22 | `cycom/cycom-erp` Next.js 16 | **~70% MVP.** Commerce core (catalog, POS + live KDS, sales/quotations, inventory, accounting w/ real journal posting, 10-step provisioning + AI-propose) built, unit-tested, several flows **live-verified in browser**. Self-serve signup wired end-to-end (proven locally against real Keycloak + payment-simulate). |
| **CyMed** — healthcare vertical | 16 (`cymed/products/cymed/`): ai_cds, clinic, commercial, core, ecosystem, fhir_r4, hospital, imaging, integrations, laboratory, mrff, patient_portal, payments, pharmacy, provider_portal, rcm | ~68k | 69 | Django portals (patient/provider) | **~40–55%, runtime-unverified.** Structurally rich: FHIR R4, revenue-cycle mgmt, labs, pharmacy, imaging (DICOM), clinical decision support. On shared `platform/` (correct). Needs clinical validation + NPHIES/PDPL-health compliance pass. |
| **CyShop** — standalone commerce | 12 (`cyshop/backend/apps/`): accounting, audit, catalog, hr, identity, inventory, notifications, payroll, pos, purchasing, sales, tenants | ~7k | **0** | `cyshop/frontend` Next.js 14 + root Vite SPA (Amplify) | **~90% duplicate of CyCom.** Own JWT auth, own tenants/accounting/hr — does **not** sit on shared `platform/`. Unique value (catalog, POS Device/receipt/KDS, quotations, onboarding UX) already harvested into CyCom. **This is the primary consolidation target.** |
| **CyMart** — marketplace layer | 6: cart, catalog, commission, orders, payments, settlement | ~3.8k | 13 | — | Phase-3 build. Order lifecycle + state machine, commission engine, cart/checkout, settlement ledger, payment-provider abstraction (refunds/disputes), wired to CyDrive dispatch. On shared `platform/`. |
| **CyDrive** — delivery company platform | 1: fleet | ~1.1k | 3 | — | Foundation only. Dispatch seam consumed by CyMart. |
| **CyVault** — object storage / archive | 1: files | ~1k | 1 | — | New. CyMed DICOM archive integration. Has prod deploy pipeline. |
| **CyEd** — education (untracked) | `CyEd/products/` | (vendored deps inflate raw count) | 111 | `CyEd/cyed-web` | Not in any status doc. Own Django project, docker-compose, SQLite fixtures. Unknown provenance — triage in Week 1. |
| **CyID / CyIdentity** — cross-tenant identity federation | `platform/cyidentity` + bridges | — | in `platform` (31 files) | mobile screens | Federation phases 3–10 in `D:\cybercom` (auth bridge, consent grants, cross-network checkout, multi-country billing JO/SA/AE/US, wallet). **Only partly in the monorepo checkout.** |
| **platform/** — shared core | api, audit, common, cyai, cydata, cyidentity, cyintegrationhub, events, notifications, observability, provisioning, security, tenant, terminology, wallet | ~28k | 31 | — | The real spine. `cyidentity` (realms, MFA, WebAuthn, break-glass), `tenant` (subscriptions, licensing, SSO, compliance), `provisioning` (industry templates + dept/country packs + blueprint→provision + AI-propose), events (outbox), notifications, observability. **CyMed + CyMart use it; CyShop + CyCom federation planned, not wired.** |
| **mobile/** — React Native shell | `cybercom-mobile-shell` RN 0.74 | — | — | ~31 TS files | Super-app foundation; real CyMart mobile experience; CyID wallet/healthcare/e-Rx screens. |
| **website/** — marketing + portals | Turbo monorepo (apps, portals, packages) | — | — | Next.js | Unified marketing site, partner portal, customer portal, licensing/marketplace guides. Wired to real subscription/sandbox backend. |

### Infra / deploy assets present

- `infrastructure/`: Caddyfile (+ demo), Dockerfiles (cycom, cymed, cyvault), 8 docker-compose files (cycom-api, cycom-dev, cyvault-api, keycloak-prod, demo-box, prod-box, api), keycloak prod runbook.
- CI: root `.github/workflows/` — deploy-backend, deploy-cycom-backend, deploy-cyshop, deploy-cyvault, deploy. Per-product: cymed (build-and-push, ci, security-scan), cyshop (ci, deploy).
- `D:\cybercom` additionally has OCI single-box deploy tooling (`feat/oci-demo-deploy`).

### Cross-cutting status

| Concern | State |
|---|---|
| Multi-tenant isolation | Queryset-level (`TenantScopedModelViewSet`) + `TenantScopedReadMixin`; Postgres RLS GUC path exists. Cross-tenant read leak **fixed in `D:\cybercom`** (not yet in monorepo). |
| Auth (prod) | Real OIDC/Keycloak; requires the Docker stack to run. `unmanagedAttributePolicy` enabled so shared-realm signups carry `tenant_id`. |
| Auth (dev) | `dev-auth` fake-JWT shim — must be `0` in prod (masked 2 real middleware bugs, since fixed). |
| Payments | **Seam + endpoints only.** No live gateway wired. Manual bank-transfer invoice today. Stripe webhook HMAC verify added (in `D:\cybercom`). |
| RTL / Arabic | **Greenfield.** `LocaleDirection` foundation added; no i18n library, no catalogs, hardcoded English, `en-US` formatting. Full bilingual = its own workstream. |
| Hosting / Odoo.sh-equivalent | **Not built.** In-app provisioning engine exists; no git-branch env / one-click operated tenant platform. |
| Payroll localization | JO + SA (GOSI) + UAE (gratuity/GPSSA) coded; **2 rates flagged for founder confirmation** (SA scheme choice, UAE national %). |
| ZATCA Phase 2 e-invoicing | **Not implemented.** Mandatory for KSA VAT-registered tenants by 2026-06-30 (already past — compliance gap for any KSA customer). |
| Automated tests | Uneven. Strong: catalog/POS/sales/accounting/CRM/payroll (~53 green in `D:\cybercom`). Thin/none: cyshop (0), cydrive, cyvault, large parts of cymed. |

---

## Artifact catalog (Section I)

Produced in this package: **executive synthesis (A) · market gap sheet (B) · canonical architecture blueprint + component & deployment diagrams (C) · canonical ERD brief + core API contracts + 3→1 migration playbook (D) · 4 vertical flavor MVP blueprints + cross-domain workflow catalog (E) · architecture-council governance charter + security controls matrix + Gulf regulatory map (F) · 12–18-month rollout milestone chart (G) · NFR checklist with testable thresholds (H) · constraints/assumptions block + go/no-go decision gates (J) · 90-day sprint plan (K)**.

To be produced during Phase 0–1 (owners in `G`): OpenAPI 3.1 spec set · event schema registry (AsyncAPI) · UI pattern library / design-system package · full data-migration runbook per source schema · risk register (living) · QA plan + coverage targets · security policy + threat model (STRIDE per service) · K8s deployment manifests + Helm charts · GitOps repo structure · developer-portal IA + content plan.

---

## Related existing docs (keep, supersede where noted)

- `SYSTEM_INVENTORY.md`, `MARKET_READINESS.md`, `GAP_ANALYSIS.md` — 2026-08-25, CyCom-scoped. **Superseded** by this package's baseline + B; keep for history.
- `BUSINESS_PLAN.md` — 2026-08-31, CyCom Commerce launch. Still valid as the **go-to-market** layer under this platform plan.
- `GO_LIVE.md` — CyCom prod deploy runbook. Folds into `K` Week 1–2 and `C` deployment blueprint.
- `RTL_AUDIT.md` — Arabic/RTL roadmap. Feeds `E` UX patterns + `H` accessibility NFRs.
- `PROJECT_STATE.md` — delivery log. Continue it; note the checkout-divergence correction.
- `docs/architecture/IDENTITY_FEDERATION.md`, `docs/security/THREAT_MODEL.md`, `docs/api/API_STANDARDS.md`, `docs/ai/AI_GOVERNANCE.md` — existing, verified-against-code. Inputs to C/D/F.
