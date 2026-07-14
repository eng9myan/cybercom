# Cycom ERP — State-of-Codebase Audit

**Date:** 2026-06-15
**Scope:** `D:\Cycom ERP - Copy\cycom-erp` (frontend) and `D:\Cycom ERP - Copy\cycom-backend` (backend).
**Files audited:** ~10 backend Python files, 60 frontend TS/TSX files (~14,400 lines), plus config.

---

## 1. Executive summary

Cycom ERP is currently a **polished frontend mockup of an ERP with one real backend feature (eSign)**. It is not an ERP product in any operational sense yet. Specifically:

- The backend implements **3 routers** (`auth`, `users`, `sign`) on SQLite, with **no authentication enforcement on any endpoint**, a hardcoded JWT secret, wildcard CORS, and a path-traversal-vulnerable file upload.
- The frontend has **~30 module folders** with substantive UI and working **client-side** business logic (POS rounding, payroll lateness/OT formulas, accounting auto-reconciliation, warehouse access checks, etc.), but only the **eSign** module actually calls the backend. Every other module operates on hardcoded `INITIAL_*` data held in `useState`; nothing persists across a page refresh.
- "Multi-company" is hardcoded source data (`context/CompanyContext.tsx`). "Login" (`app/login/page.tsx`) is a `setTimeout` that redirects to `/` regardless of credentials.

The gap between this and "more powerful than SAP/Oracle/Workday" is structural, not feature-list-deep. The honest path forward is to (a) stabilize the backend platform, (b) wire the existing UI to real APIs one module at a time, (c) only then talk about feature parity with mature ERPs.

---

## 2. What's actually built

### 2.1 Backend (`cycom-backend/`)

| Area | Status | Files |
|---|---|---|
| Web framework | FastAPI 1 app, CORS open | [app/main.py](cycom-backend/app/main.py) |
| Persistence | SQLAlchemy ORM on **SQLite** (`cycom_erp.db`, 53 KB) | [app/db/session.py](cycom-backend/app/db/session.py), [app/core/config.py](cycom-backend/app/core/config.py) |
| Auth | JWT issuance (HS256, 7-day expiry) | [app/core/security.py](cycom-backend/app/core/security.py), [app/api/routers/auth.py](cycom-backend/app/api/routers/auth.py) |
| Users & Roles | CRUD users, CRUD roles (no auth required to call) | [app/models/user.py](cycom-backend/app/models/user.py), [app/api/routers/users.py](cycom-backend/app/api/routers/users.py) |
| eSign | Upload PDF template, create sign request, public-token signing flow | [app/models/sign.py](cycom-backend/app/models/sign.py), [app/api/routers/sign.py](cycom-backend/app/api/routers/sign.py) |
| Migrations | **None** — `Base.metadata.create_all()` at import time | [app/main.py:11](cycom-backend/app/main.py) |
| Dependency manifest | **None** — no `requirements.txt` / `pyproject.toml`; only `venv/` | — |
| Tests | **None** | — |

**No backend implementation exists for:** accounting, attendance, payroll, HR, inventory, sales, purchase, POS, CRM, projects, manufacturing/PLM, fleet, helpdesk, recruitment, expenses, planning, marketing, knowledge, documents, discuss, maintenance, quality, subscriptions, portal. ~27 of 30 frontend modules have **zero backend support**.

### 2.2 Frontend (`cycom-erp/`)

Next.js 16 + React 19 + Tailwind 4 + Radix UI + Recharts + Framer Motion. ~14.4K lines across 60 files.

**Module-by-module status:**

| Module | Files | Lines | Backend wired? | Persistence | Notes |
|---|---|---|---|---|---|
| `app/page.tsx` (launcher) | 1 | 98 | n/a | n/a | Hardcoded module list |
| `app/login/page.tsx` | 1 | 114 | **No** | n/a | `setTimeout(1s) + router.push('/')` — fake login |
| `app/dashboard/page.tsx` | 1 | 139 | No | n/a | Hardcoded `GRAPH_DATA`, `ALERTS` |
| `app/sign/**` | 5 | 1,267 | **Yes** | Backend | Only module wired to API |
| `app/accounting/**` | 3 | 653 | No | useState | Mock journal entries, auto-reconciliation logic in-browser |
| `app/attendance/**` | 4 | 818 | No | useState | Mock ZK devices, geofence form, OT calculator |
| `app/crm` | 1 | 296 | No | useState | Mock contacts/leads |
| `app/discuss` | 1 | 348 | No | useState | Mock messages |
| `app/documents/page.tsx` | 1 | 847 | No | useState | DMS UI + canvas signature draw |
| `app/expenses` | 1 | 357 | No | useState | Mock expense claims + approval queue |
| `app/fleet` | 1 | 426 | No | useState | Mock vehicles |
| `app/helpdesk` | 1 | 292 | No | useState | Mock tickets |
| `app/hr/**` | 6 | 951 | No | useState | Hardcoded `EMPLOYEES` array (4 records) |
| `app/inventory/**` | 3 | 640 | No | useState | Mock transfers + warehouse access logic |
| `app/knowledge` | 1 | 346 | No | useState | Mock articles |
| `app/maintenance` | 1 | 317 | No | useState | Mock equipment |
| `app/marketing` | 1 | 294 | No | useState | Mock campaigns |
| `app/payroll/**` | 4 | 730 | No | useState | Working lateness/OT calc in browser |
| `app/planning` | 1 | 317 | No | useState | Mock schedule |
| `app/plm` | 1 | 370 | No | useState | Mock BOM |
| `app/portal/**` | 4 | 701 | No | useState | Self-service stubs |
| `app/pos/**` | 4 | 1,083 | No | useState | Full POS UI with cart/payment flow, all client-side |
| `app/project` | 1 | 328 | No | useState | Mock kanban |
| `app/purchase` | 1 | 382 | No | useState | Mock POs |
| `app/quality` | 1 | 240 | No | useState | Mock checks |
| `app/recruitment` | 1 | 289 | No | useState | Mock candidates |
| `app/sales/**` | 3 | 713 | No | useState | Mock orders + discount-exception approval logic |
| `app/settings` | 1 | 58 | No | useState | Stub |
| `app/subscriptions` | 1 | 334 | No | useState | Mock subs |
| `components/layout/**` | 3 | 346 | n/a | n/a | Sidebar, topbar, wrapper |
| `context/CompanyContext.tsx` | 1 | 89 | n/a | n/a | **Hardcoded** 3 companies + 23 hardcoded "Anabtawi" store names |

**Per-module legend:**
- "Backend wired" = at least one `fetch` to `/api/*` exists. Only `app/sign/**` passes this test.
- "useState" persistence means data lives in the React component and is lost on refresh; there is no localStorage, no IndexedDB, no API.

---

## 3. Architecture & security risks

Listed with file references. Severity: 🔴 critical, 🟠 high, 🟡 medium.

### 3.1 Authentication & authorization
- 🔴 **No endpoint requires authentication.** None of the routes in [users.py](cycom-backend/app/api/routers/users.py) or [sign.py](cycom-backend/app/api/routers/sign.py) declare `Depends(oauth2_scheme)` or a `get_current_user` dependency. An unauthenticated caller can list all users ([users.py:31](cycom-backend/app/api/routers/users.py)), create a superuser ([users.py:12-29](cycom-backend/app/api/routers/users.py)), create roles, upload sign templates, and list all signature requests.
- 🔴 **JWT secret hardcoded in source** at [security.py:9](cycom-backend/app/core/security.py): `SECRET_KEY = "cycom-super-secret-key-for-development-only"`. Anyone with source-code access can forge any user's token. Not loaded from env.
- 🔴 **Login on the frontend never authenticates.** [login/page.tsx:15-22](cycom-erp/app/login/page.tsx) is `setTimeout(1000) → router.push('/')`. No call to `/api/auth/login`, no token stored. Hitting `/` works without credentials.
- 🟠 **Permissions are defined but unused.** `Role.permissions` is a JSON list, but no decorator/dependency ever reads it.

### 3.2 Input handling
- 🔴 **Path traversal in eSign upload.** [sign.py:25](cycom-backend/app/api/routers/sign.py) does `os.path.join(UPLOAD_DIR, file.filename)` with no sanitization. `file.filename = "../../app/main.py"` overwrites source. (FastAPI `UploadFile.filename` is attacker-controlled.)
- 🟠 **Untyped signature payload.** [sign.py:79](cycom-backend/app/api/routers/sign.py) accepts `signature_data: dict` — no Pydantic schema, no size limit, no content validation.

### 3.3 Network & transport
- 🟠 **CORS wildcard with credentials.** [main.py:23-29](cycom-backend/app/main.py) sets `allow_origins=["*"]` + `allow_credentials=True`. Browsers reject this combination, masking the misconfiguration; the intent is broken either way.
- 🟡 **API base URL hardcoded** as `http://localhost:8000` in every eSign frontend file ([sign/page.tsx:20-23](cycom-erp/app/sign/page.tsx), [sign/templates/page.tsx:35,84,111](cycom-erp/app/sign/templates/page.tsx), [sign/requests/page.tsx:16,20](cycom-erp/app/sign/requests/page.tsx), [sign/public/[token]/page.tsx:34,121](cycom-erp/app/sign/public/[token]/page.tsx)). No `NEXT_PUBLIC_API_URL`.

### 3.4 Data layer
- 🔴 **SQLite as the primary database.** [config.py:9](cycom-backend/app/core/config.py). File-locking single-writer, no concurrent writes, no replication. Disqualifies the platform from any multi-user production use.
- 🟠 **No migrations.** [main.py:11](cycom-backend/app/main.py) calls `Base.metadata.create_all(bind=engine)` at import time. Any model change either silently no-ops on existing tables or requires DB drop. No Alembic.
- 🟠 **No multi-tenancy at the data layer.** [user.py](cycom-backend/app/models/user.py), [sign.py model](cycom-backend/app/models/sign.py) have no `company_id` / `tenant_id`. The frontend "company switcher" is decorative.
- 🟡 **No audit log / change tracking** anywhere.

### 3.5 Operational
- 🟠 **No dependency manifest in backend.** No `requirements.txt`, no `pyproject.toml`. Reproducing the environment requires guessing from imports.
- 🟠 **No tests.** Zero test files in either project.
- 🟡 **No env example.** Frontend has no `.env.example`; backend reads no env vars at all.
- 🟡 **Schema management via side effect** ([main.py:11](cycom-backend/app/main.py)).

### 3.6 Frontend architecture
- 🟡 **Tenant baked into UI.** [login/page.tsx:44](cycom-erp/app/login/page.tsx) ("Anabtawi Group Portal"), [topbar:46](cycom-erp/components/layout/CycomTopbar.tsx) ("ZK Biometric Sync Active"), [CompanyContext.tsx:16-54](cycom-erp/context/CompanyContext.tsx) (23 hardcoded "Anabtawi" stores). If multi-tenant is a real goal, all of this is throwaway.
- 🟡 **No global state management.** ~14K lines of `useState`; no Redux/Zustand/Jotai/React-Query/SWR. Future API integration will mean rewriting every page.
- 🟡 **Next.js 16 + React 19** — extreme cutting edge. [AGENTS.md](cycom-erp/AGENTS.md) warns that conventions differ from training data; ecosystem support is still maturing.

---

## 4. The honest gap to "world-class ERP"

The original prompt frames Cycom as a candidate replacement for SAP / Oracle / Workday / NetSuite / Cycom. The realistic baseline:

- **Cycom 19** = ~10M+ lines, ~80 core modules, ORM with computed fields/onchange/depends, automated actions, multi-company, EDI, OCA ecosystem. 20 years of work.
- **SAP S/4HANA** = decades of work, tens of thousands of engineers, industry-specific configuration.
- **Workday** = ~15 years of work on a purpose-built object-data-model.

**Current Cycom** = 1 working backend feature (eSign), ~30 client-side UI mockups, no migrations, no tests, no real auth, no real persistence outside eSign, no multi-tenancy.

Producing a "feature matrix vs. SAP" or "200-page gap analysis" against this baseline would be a fiction-writing exercise. The deliverables in the original prompt only become real once a viable platform exists underneath them.

---

## 5. Recommended 90-day roadmap

This roadmap is what an enterprise-software team would actually do. It assumes one or two competent engineers working full-time; adjust accordingly.

### Phase A — Stabilize the platform (weeks 1–4)
Goal: a backend you can safely deploy and build on.

1. **Backend dependency manifest** — add `pyproject.toml` (or `requirements.txt` + `requirements-dev.txt`). Lock versions.
2. **Configuration via environment variables** — move `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, allowed CORS origins, JWT expiry into `pydantic-settings` with a `.env.example`. Refuse to start with default secrets in non-dev.
3. **Replace SQLite with PostgreSQL.** Single-line change in `config.py` once the URL is env-driven, plus `psycopg[binary]` dependency. Keep SQLite as an optional dev fallback only.
4. **Add Alembic** and snapshot existing schema as migration `0001_initial`. Stop calling `Base.metadata.create_all` at startup.
5. **Enforce auth on every endpoint** — implement `get_current_user(token = Depends(oauth2_scheme))` dependency; wire it onto every router. Add `get_current_superuser` for admin routes.
6. **Tighten CORS** — derive `allow_origins` from env; drop `*`.
7. **Fix eSign path traversal** — use `uuid4().hex + Path(file.filename).suffix`, reject suffixes outside `{".pdf"}`.
8. **Add multi-tenancy at the data layer** — `Company` model; `company_id` FK on `User`, `SignTemplate`, `SignRequest`; query scoping helper.
9. **Wire the frontend login to the real API** — replace the `setTimeout` with `fetch('/api/auth/login')`, store JWT in httpOnly cookie (server route) or memory + refresh token, add a fetch interceptor that attaches `Authorization: Bearer`.
10. **Add a CI pipeline** (GitHub Actions or similar): lint, type-check, run tests (even if there are none yet — the scaffold matters).

**Exit criterion for Phase A:** an unauthenticated request to anything other than `/api/auth/login` returns 401. A fresh checkout boots cleanly via documented commands. CI is green.

### Phase B — Pick ONE module and build it end-to-end (weeks 5–9)
Goal: a single domain that works for real and proves the architectural pattern.

Recommended pick: **HR + Attendance + Payroll** as a vertical slice — it's the cluster the frontend has invested most in and has the cleanest scope (Employee + Department + Attendance log + Payslip).

For the chosen slice, deliver: backend models, migrations, Pydantic schemas, authenticated CRUD, list filters with pagination, audit log, RBAC, frontend rewired to API with optimistic updates and error handling, unit tests on the calculation logic (lateness, OT), end-to-end tests on the critical flow, deployment runbook.

**Exit criterion for Phase B:** an HR admin can log in, add an employee, record attendance, run payroll for a period, view the payslip; all of it survives a server restart; tests pass.

### Phase C — Replicate the pattern (weeks 10–13)
Goal: two more modules following the established pattern, plus reporting.

Suggested: **Inventory** (already has substantive UI) and **Sales** (already has discount-exception logic). Add a generic reporting layer (parameterized SQL or a thin BI layer, e.g. Cube or Metabase) instead of inventing one.

**Exit criterion for Phase C:** three modules in production-shape, reporting on each, clear contributor guide for adding module #4.

### What is NOT in this 90-day plan, and why
- AI assistants, voice control, predictive analytics — these are layered on top of working modules with real data; they cannot exist without them.
- Manufacturing, PLM, fleet, helpdesk, marketing, CRM, projects, etc. — every module follows the same pattern as Phase B; sequencing is a business decision.
- Multi-country payroll, IFRS consolidation, EDI, SOC2 — months of work each, scope-dependent. Add to the backlog; tackle when a real customer needs them.
- "Match Cycom / SAP / Oracle feature-for-feature" — not a tractable goal for a single team. Pick the verticals you care about and beat them in those.

---

## 6. What I'd recommend doing next (in this conversation)

Three useful next steps, in increasing depth — pick whichever fits your time:

1. **Have me execute Phase A items 1–7** on the actual codebase right now: pyproject + env config + Postgres URL switch + Alembic baseline + auth dependency wired onto every endpoint + CORS tightening + path-traversal fix. Concrete code changes, no more documents. ~1–2 hours.
2. **Have me execute the Phase B vertical slice** for HR/Attendance/Payroll: models, migrations, auth-gated CRUD, frontend rewired, tests. Substantial — a focused session.
3. **Have me write Architecture Decision Records** (ADRs) for the major choices in the roadmap (Postgres vs. alternatives, JWT vs. session, multi-tenancy strategy, RBAC vs. ABAC, Alembic vs. alternatives, state management on frontend). Useful if you want to socialize the plan with stakeholders before code lands.

I do not recommend producing more comparison documents against SAP / Oracle / Workday until at least Phase A is real. Until then the comparison is between a prototype and shipping products, and the document writes itself: "everything is missing."

---

*Appendix: this audit was performed by reading every source file in both projects. Module status was determined by grepping for `fetch(` and `/api/` across the frontend; only the eSign module had hits. Risk file:line references were verified during the read.*
