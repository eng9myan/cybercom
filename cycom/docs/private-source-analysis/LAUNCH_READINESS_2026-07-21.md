# Cycom ERP — Launch Readiness & Corrected Gap Analysis
# Copyright (C) CyberCom. All rights reserved.
# Generated: 2026-07-21 (supersedes the 2026-07-14 audit set on architecture facts)

> **Why this doc exists:** the 2026-07-14 docs in this folder
> (`CYCOM_CURRENT_STATE`, `FEATURE_PARITY_MATRIX`, `IMPLEMENTATION_ROADMAP`)
> describe a **retired** backend (FastAPI + SQLite, "~5% complete, only eSign
> wired"). The codebase has since pivoted **twice**. Those documents are
> obsolete on architecture and completeness. This doc records verified
> current reality as of 2026-07-21.

---

## 1. Which version is canonical

| Copy | Age | Verdict |
|---|---|---|
| **`D:\cybercom\cycom`** | 2026-07-21, 220 commits | **Canonical.** Superset — same Next.js frontend PLUS the Django backend, `compliance-gateway/`, CyID phases. Build here. |
| `D:\Cycom ERP` | 2026-07-15, 19 commits | Stale snapshot. Do not build on it. |

## 2. Verified current architecture

Backend lineage: FastAPI → Odoo-19 fork → **Django 6 + DRF (current)**.
Both the README (says Odoo) and the 07-14 audit (says FastAPI) are stale.

- **Backend:** Django 6.0.7 + DRF, PostgreSQL 16, Redis, Celery, **Keycloak**
  (OIDC, RS256 via JWKS), multi-tenant (`X-Tenant-ID` header + `tenant_id`
  UUID claim, queryset-level scoping in `core.viewsets.TenantScopedModelViewSet`).
  OpenAPI docs at `/api/docs/`.
- **Frontend:** Next.js 16 + React 19, Tailwind 4 + Radix + Framer Motion.
  Talks to Django through `/api/cycom/*` proxy route handlers.

### Backend size (measured, not estimated)
| Metric | Count |
|---|---|
| Product domains (`products/cycom/*`) | 29 |
| Product model classes | 180 |
| Shared platform model classes (`platform/*`) | 278 |
| **Total model classes** | **~458** |
| DRF ViewSets / registered endpoints | 52 |
| Realized migrations (products) | 35 |
| Backend tests | 46 (all passing) |

API domains live: accounting, ar_ap, hr, payroll, inventory, access, pos, crm,
procurement, documents, expenses, scheduler, notes, todo, knowledge,
manufacturing, maintenance, quality, field_service, subscriptions, equity, esg,
localization, + 5 CyAI agent domains, + platform identity/events/audit/ai.

## 3. Launch-readiness verification (done 2026-07-21)

| Check | Result |
|---|---|
| `manage.py check` (all 29 apps) | ✅ 0 issues |
| Backend test suite (SQLite `settings_test`) | ✅ 46 passed |
| Frontend dev server (`npm run dev`, :3000) | ✅ Live, renders app launcher + module pages |
| Wired page behavior w/o auth (HR Employees) | ✅ Graceful: "backend → 401: Not authenticated" |
| Live end-to-end (Postgres+Redis+Keycloak) | ⛔ **Blocked**: local Docker daemon wedged this session |

**Bottom line:** backend is real, coherent, and tested; frontend launches. The
platform is *far* past the "5% prototype" the old audit claims. The remaining
launch blockers are (a) infra bring-up and (b) the UI↔backend integration gap.

## 4. The #1 issue — UI↔backend integration gap

The backend exposes ~52 REST endpoints; the UI still speaks the **retired
Odoo-shaped `{model,method,args,kwargs}` RPC**, bridged by `lib/cycomServer.ts`.
That shim maps only **6 models**:

`crm.lead`, `hr.employee`, `account.move`, `cy.vendor`, `inventory.product`,
`cy.internal.order(.line)` (+ `cy.vendor.document` stubbed to `[]`).

Everything else the UI calls returns **HTTP 501 "not yet migrated"**.

Frontend reality (81 `page.tsx` total):
- **16 pages** actually call the backend.
- **~6 models** succeed; the rest (`fleet.vehicle`, `cy.fleet.*`,
  `finance.invoice`, `ir.config_parameter`, …) **501**.
- **~65 pages** are static / client-side mock (no backend at all).

So the gap is not a missing backend — it's a **missing UI-to-API rewiring
layer**. High leverage: the data already exists server-side.

## 5. Comparison framing (Odoo 19 / Anabtawi / ERPGo)

| Reference | What it is | Use for Cycom |
|---|---|---|
| **Odoo 19** (`D:\odoo-19.0`) | Reference ERP | Feature baseline — the 07-14 `FEATURE_PARITY_MATRIX` scored Cycom vs Odoo ("Ref-A") across 202 features. Still valid as a *feature* checklist; its *status* column is stale (understates Cycom). |
| **Anabtawi** (`D:\Anabtawi-Group-main`) | ~92 Odoo custom modules — Jordan localization (ZATCA/JoFotara e-invoicing, ZK biometric attendance, POS pledge/rounding, payroll SS) | Source of the region-specific requirements Cycom must match. Maps to `products/cycom/localization` + `compliance-gateway/`. |
| **ERPGo files** (`D:\Erp go files`) | Laravel + React **hospital system (CyMed)** — patients, pharmacy, WHO ICD-11 | ⚠️ **Not an ERP competitor.** Different vertical (healthcare); a sibling product in the CyberCom monorepo, not a parity benchmark. Excluded from feature scoring. |

## 6. UI / UX findings (from source, 2026-07-21)

Design language is modern (Tailwind 4, Radix primitives, Framer Motion, glass /
card-based, orange+blue brand). But concrete defects found in the code:

**Functional (worst first)**
- **Most screens show fake data or an error card.** ~65 mock pages + ~10 501
  pages. Reads as "broken" regardless of visual polish. This is the dominant
  UX problem and is downstream of §4 (the wiring gap).
- **No RTL / i18n despite Arabic being a core market.** `layout.tsx` hardcodes
  `<html lang="en">`, no `dir` attribute, no i18n framework — yet the backend
  ships `LANGUAGES=[en,ar]`, tenants default `locale="ar"`, and Anabtawi/JO/SA
  are RTL. This blocks the target market. High priority.
- **RBAC not applied in the UI.** The app launcher (`app/page.tsx`) shows all 18
  modules to everyone; its own comment says permission filtering is "in the
  future." No client-side gating on modules/actions.

**Design-system consistency**
- **Three different dark backgrounds:** body `#030712` (`layout.tsx`),
  `--background` `oklch(0.09…)` (`globals.css`), launcher `#0a0f1e`
  (`page.tsx`). Pick one token.
- **Design tokens defined but bypassed.** `globals.css` has a real system
  (`.glass-card`, `.btn-primary`, `.badge-*`, `.data-table`, `.input-field`),
  but pages use raw arbitrary Tailwind (`bg-white/5`, `from-blue-500`) instead.
  Drift between the token layer and the pages.
- **Dead token:** `--font-sans: var(--font-inter)` but `--font-inter` is never
  defined (no `next/font`).

**Performance / accessibility**
- **Inter is fetched twice from Google Fonts** — a `<link>` in `layout.tsx`
  AND an `@import url()` in `globals.css`. Both are render-blocking external
  CDN calls (privacy/GDPR + offline-break). Move to `next/font/google` (self-
  hosted, one copy).
- **No `prefers-reduced-motion`.** Infinite `pulse-ring` keyframes + pervasive
  Framer Motion never idle (confirmed: screenshot-on-idle never settles).
  Accessibility + perf issue.
- Icon-only nav and search input lack visible labels; badges signal by color
  only; `slate-500`-on-dark body text is a likely WCAG contrast fail.
- Dark-mode-only (`color-scheme: dark`), no theme toggle — fine as a choice,
  but note it's hardcoded, not tokenized.

**Good, keep:** error states are graceful (clear message + remediation hint);
the token system and brand palette are solid once actually used; layout is
responsive (grid breakpoints on the launcher).

Pixel/interaction pass on live data is scheduled after §7 step 1 (wiring).

## 7. Prioritized launch plan

**0. Unblock infra (prereq).** Restart the Docker daemon, then:
```
docker compose -f infrastructure/docker-compose.cycom-dev.yml up -d
```
(Dev compose added this session: Postgres + Redis + Keycloak with realm
auto-import. Django runs on the host; `.env.local` for the frontend added.)
Remaining infra to finish: a `cybercom` realm-import JSON with a `tenant_id`
token mapper = the seed tenant UUID `11111111-1111-1111-1111-111111111111`,
and a matching `Tenant` row seeded in Postgres.

**1. Close the UI↔backend 501 gap** *(highest leverage — backend already exists)*.
Rewire the 16 API pages + expand `MODEL_ADAPTERS` (or, better, retire the
Odoo-shaped shim and call `/api/v1/*` directly). Order by business value:
inventory, accounting, procurement, pos, payroll.

**2. UI/UX audit pass** on now-live pages (after step 1). Reduced-motion,
loading skeletons, empty vs error states, RTL/Arabic.

**3. Three mandatory workflows** end-to-end:
   1. Supplier onboarding → PO → 3-way match → payment
   2. Branch internal orders (allocation / backorder / discrepancy)
   3. Bulk employee Excel import (dry-run validation)

**4. Security hardening** before any real launch: the 07-14
`SECURITY_GAP_ANALYSIS` items that still apply to the Django stack (rate
limiting on auth proxy, upload sanitization, audit immutability, CORS in prod).

## 8. What is NOT true anymore (correcting the record)
- ❌ "FastAPI + SQLite backend" → now Django 6 + Postgres.
- ❌ "Only eSign has real persistence / ~5% complete" → 458 models, 52
  endpoints, 46 passing tests.
- ❌ "No RBAC / no tenant isolation" → Keycloak RS256 + per-request tenant
  scoping middleware exist and are exercised by tests.
- Still true: the **frontend** is largely unwired to the backend, and infra/
  security hardening for production is incomplete.
