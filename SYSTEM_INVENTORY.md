# SYSTEM_INVENTORY.md — CyberCom Platform (verified against source, 2026-08-25)

> Ground-truth inventory of the three products as they actually exist in `D:\cybercom`.
> Corrects several assumptions in the buildout prompt (stack, product separation).

## Stack (verified — prompt was wrong)

The buildout prompt states the stack is **Laravel / Inertia / React / PostgreSQL**. It is not.

| Layer | Actual |
|---|---|
| Backend | **Django + Django REST Framework** (`manage.py`, `core/settings.py`; no `artisan`/`composer.json`) |
| Frontend | **Next.js 16.2.9** (App Router, TypeScript) — `cycom/cycom-erp` |
| Shared platform | `platform/` Django apps (identity, tenant, provisioning, audit, events, notifications, cyai, …) |
| DB | PostgreSQL in prod; SQLite for the no-Docker dev/demo path |
| Auth | OIDC/Keycloak claims via middleware (prod); dev-auth fake-JWT shim for local/demo |

Any launch-repo scaffold must be Django+Next, **not** Laravel/Inertia.

## Architecture (verified)

- **Shared `platform/`** = the real core: `cyidentity` (26 models: realms, MFA, WebAuthn, break-glass), `tenant` (26 models: subscriptions, licensing, SSO, compliance), `provisioning` (industry templates + dept/country packs + blueprint→provision engine + AI-propose), `audit`, `events`, `notifications`, `cyai`, `common` (BaseModel, tenant scoping).
- **CyCom** (`cycom/`, 39 product apps) — general ERP on shared platform. Django backend + Next.js ERP UI.
- **CyMed** (`cymed/`, 16 product apps) — healthcare vertical **on the same shared `platform/`** (inherits correctly, does NOT duplicate core).
- **CyShop** (`cyshop/`, 12 apps) — **standalone, own backend** (`cyshop/backend/apps`), own JWT auth, own `tenants`/`identity`/`accounting`. **Does NOT sit on shared platform.** → This is the P0 architectural finding the prompt asked to check for.

## Product-by-product

### CyCom — 39 apps (most mature; the one I've been in all session)
access, accounting, ar_ap, catalog*, crm, cyai_*, discuss, documents, equity, esg, expenses, field_service, fleet, helpdesk, hr, inventory, knowledge, leave, localization, maintenance, manufacturing, marketing, notes, payroll, planning, plm, pos, procurement, project, quality, recruitment, sales, scheduler, subscriptions, todo.
- **Verified working + tested this session**: catalog (ported from CyShop), POS (+ Device/PosReceipt/KDS kitchen flow), sales (quotations, retail/wholesale), inventory, provisioning wizard (10-step, industry templates, AI-propose, blueprint→provision), accounting/AR-AP with real journal posting.
- **Self-serve signup**: wired (public `demo/` + `register/` endpoints, frontend `/signup`) — completion blocked only by Keycloak in no-Docker.
- **Demo**: `seed_demo_commerce` + `seed_demo_business` produce a fully-populated tenant; KDS/onboarding/POS verified live in-browser.

### CyMed — 16 apps (structurally rich; runtime unverified this session)
ai_cds, clinic, commercial, core, ecosystem, fhir_r4, hospital, imaging, integrations, laboratory, mrff, patient_portal, payments, pharmacy, provider_portal, rcm.
- Healthcare vertical: hospital/clinic ops, FHIR R4, labs, imaging, pharmacy, revenue-cycle mgmt, patient/provider portals, clinical decision support, payments.
- On shared platform (good). **Not runtime-verified in this session** — depth of "functional + tested" needs its own audit pass.

### CyShop — 12 apps (being absorbed into CyCom)
accounting, audit, catalog, hr, identity, inventory, notifications, payroll, pos, purchasing, sales, tenants.
- ~90% duplicates CyCom/platform (own auth, own tenants, own accounting/hr/payroll/inventory).
- **Unique value already harvested into CyCom this session**: `catalog` app, `pos.Device`/`PosReceipt`/KDS, `sales` quotations + retail/wholesale, self-serve onboarding UX.
- **Recommendation: not a separate product.** Fold remaining value into CyCom as the "Commerce" industry template; archive the standalone repo. (Merge already in progress — see `project_cyshop_cycom_merge`.)

## Cross-cutting status

| Concern | State |
|---|---|
| Multi-tenant isolation | Enforced at queryset level (`TenantScopedModelViewSet`); RLS GUC path exists for Postgres |
| Auth (prod) | OIDC/Keycloak — real, but requires the Docker stack to run |
| Auth (demo/dev) | dev-auth fake-JWT shim — works, no Keycloak |
| Payments | **Missing** — `register` issues a bank-transfer-pending invoice; no gateway |
| RTL/Arabic | Partial; not audited this session |
| Hosting/Odoo.sh-equivalent | Not built (provisioning engine exists in-app; no git-branch env platform yet) |
