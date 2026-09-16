# CyEd — Buyer-Audit Gap Closure

Response to the "chain-of-schools in Australia" buyer audit. Every gap that is
**code-buildable** is now built, migrated, and tested. Items that require
**credentials, contracts, or third-party certification** (not code) are wired to
seams and listed under "External" with the exact action required.

Baseline before this phase: 129 backend tests. After: **147 passing**, `manage.py
check` clean, frontend `tsc` + `next build` clean.

---

## 1. Multi-campus / group layer  ✅ built

The tenant is the **group**; campuses are units beneath it.

- `cyed.org` app — `Campus` model (name, code, address, state, principal, …),
  unique code per group (non-blank only).
- `campus` FK added to `Student`, `ClassSection`, `Staff`, `StudentBill`
  (nullable → existing data unaffected).
- `GET /api/v1/org/rollup/` — consolidated group view: per-campus student /
  staff / class counts + outstanding fees, plus group totals and an
  "unassigned campus" figure. Leadership/office only.
- Campus RBAC scoping helpers (`campus_ids`, `scope_queryset_by_campus`) for
  campus-bound staff (via a `campus_ids` session claim).
- CRUD at `/api/v1/org/campuses/` (staff write, authenticated read).

## 2. AU statutory reporting  ✅ built

- Student demographics for the national collections: `usi`,
  `state_student_number`, `indigenous_status` (ABS standard), `country_of_birth`,
  `language_at_home`, `lbote`, parental education/occupation (SES).
- `cyed.compliance` app:
  - `NCCDRecord` — disability category + level of adjustment, unique per student
    per collection year. Pastoral/leadership only.
  - Exports (leadership/office only, CSV or JSON, every run logged to
    `StatutoryReportLog`):
    - `exports/nccd/` + `exports/nccd-summary/` — NCCD return + counts.
    - `exports/attendance/` — per-student attendance-rate return.
    - `exports/naplan/` — Year 3/5/7/9 participation cohort with USI.
    - `exports/census/` — ABS/ACARA demographic census rows.

  These produce the **data**; lodgement into the government portals (NCCD, NAP,
  state census) is a manual upload by design.

## 3. Security hardening  ✅ built (code parts)

- **Field-level encryption at rest** (`core.crypto`, Fernet, key
  `CYED_FIELD_KEY`, multi-key rotation): health record allergies / conditions /
  medications / medicare / notes, medical-incident description / treatment,
  wellbeing note, check-in response, learner-profile notes. Ciphertext in the DB,
  transparent to the ORM. No key set (dev) → plaintext fallback so tests run.
- **PostgreSQL Row-Level Security** (`governance` migration `0002`,
  Postgres-only): `ENABLE`/`FORCE ROW LEVEL SECURITY` + `tenant_isolation`
  policy keyed on `current_setting('app.current_tenant_id')` across the
  sensitive/PII tables. `ATOMIC_REQUESTS` enabled so the tenant middleware's
  `SET LOCAL` is scoped per request (no leak across the pooled connection).
  Defence-in-depth beneath the existing app-layer tenant scoping.
- **Session / auto-logout**: 30-min sliding expiry, expire-at-browser-close,
  HttpOnly + SameSite=Lax cookies.

## 4. PWA mobile + accessibility  ✅ built

- Installable PWA: `manifest.webmanifest` (standalone, theme colour, 192/512 +
  maskable icons), service worker (`/sw.js`, network-first navigations with an
  `/offline` fallback, SWR for static, **never caches `/api/*`**), registered in
  production only.
- Accessibility (WCAG 2.1 AA foundation): skip-link, `<nav aria-label>` +
  `aria-current="page"`, focusable `<main>`, visible `:focus-visible` outlines,
  `.sr-only` labels for icon-only controls, status chips that carry a glyph +
  text (never colour alone), `prefers-reduced-motion` honoured, responsive
  shell (sidebar collapses to a scrollable top bar on mobile — verified at
  375px, no horizontal overflow).

## 5. Data migration  ✅ built

- `sis.imports` — CSV importers for students and staff, **idempotent** (upsert by
  student_number / staff_number, re-run updates rather than duplicates), with a
  per-row error report and campus-code mapping.
- Endpoints `POST /api/v1/sis/students/import/` and `/api/v1/hr/staff/import/`
  (multipart `file`, staff-only) + a `/data-import` UI page with downloadable
  templates.

---

## External — not code (credentials / contract / certification)

These were called out in the audit and are **seam-ready** but cannot be
completed from the codebase:

| Item | Why it's external | Where it plugs in |
|------|-------------------|-------------------|
| Native iOS/Android app-store apps | Requires Apple/Google developer accounts + store review | PWA is installable now; a wrapper (Capacitor) can reuse `cyed-web` |
| Microsoft Entra / Google SSO | Needs the customer's tenant + client registration | Auth already validates RS256 JWT via JWKS; point issuer/JWKS at the IdP |
| Independent penetration test | Third-party engagement | Hardened surface (RLS, encryption, session, headers) ready to test |
| ST4S / IRAP assessment | Formal certification process | Data-governance, consent, audit, PII-strip, encryption controls in place |
| Licensed full ACARA v9 content load | ACARA licensing | Ingestion pipeline built (`curriculum` app); load the licensed dataset |
| Production TLS certs / WAF / backups | Deployment/ops decision | Dockerfiles + compose + `DEPLOYMENT.md` provided |

## Verify

```bash
cd D:/cybercom/CyEd
DJANGO_SETTINGS_MODULE=core.settings_test DJANGO_SECRET_KEY=test-secret \
  python -m pytest -q          # 147 passed
cd cyed-web && npx tsc --noEmit && npm run build
```
