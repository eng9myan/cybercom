# CyED ↔ CyCom — Generic ERP Reuse

> **SUPERSEDED — 2026-08-11.** This document describes a "proxy to CyCom, don't
> rebuild" strategy. That strategy was **not followed**: `products/cycom/*` does
> not exist anywhere in this repository, and CyED's own Phase 0 build (see
> `DEPLOYMENT_READINESS_2026-08-09.md`) shipped native, tested HR, Payroll,
> Staff Attendance, Accounting, Inventory, and Procurement modules directly
> inside `products/cyed/*`. Those native modules are what's real and load-bearing
> today — they are not stubs sitting alongside a working CyCom integration.
>
> The proxy code below (`products/cyed/erp/client.py`, `erp/views.py`) still
> exists and is harmless: it lives at a separate URL namespace
> (`/api/v1/erp/<path>`), does nothing unless `CYED_CYCOM_URL` is set, and
> returns `503` otherwise. It does not conflict with the native modules. But it
> is currently **dead code pointing at a product that isn't built**, not an
> active integration.
>
> **This needs a decision from the product owner, not more guessing:**
> either (a) CyCom is a real, separate product that will exist later and this
> proxy should stay dormant until then — in which case say so explicitly and
> stop referring to HR/payroll/inventory/procurement/accounting as "reused from
> CyCom" anywhere else in the docs; or (b) CyCom was abandoned as a strategy in
> favour of the native build, in which case this whole file and the `erp/` proxy
> app should be deleted to stop the next person from re-reading this and
> assuming the wrong architecture. Until that decision is made, treat the native
> `hr`, `payroll`, `staff_attendance`, `accounting`, `inventory`, and
> `procurement` apps under `products/cyed/` as the real, current implementation.

---

## Original document (as written, now describing a strategy that wasn't followed)

CyED does **not** rebuild the generic school-business ERP. Those modules already
exist, built and tested, in **CyCom** (`products/cycom/*`). CyED consumes them so a
school runs **one ecosystem**: CyCom for back-office ERP, CyED for the education
domain — both on the shared `platform/` (same CyIdentity tenant + audit).

## How the reuse works
- `products/cyed/erp/client.py` calls CyCom's REST API at `CYED_CYCOM_URL`.
- `GET/POST /api/v1/erp/<cycom-path>/` (staff-only) forwards the caller's bearer
  token + tenant, so **CyCom enforces its own RBAC and tenant isolation** — CyED
  never duplicates the data or the logic.
- Unconfigured → `503` (nothing silently faked). Non-whitelisted path → `400`.

## What is reused from CyCom (do NOT rebuild in CyED)
| School ERP need | CyCom module | Proxy path |
|---|---|---|
| Staff records, contracts | `products.cycom.hr` | `/api/v1/erp/hr/...` |
| Payroll | `products.cycom.payroll` | `/api/v1/erp/payroll/...` |
| Staff leave | `products.cycom.leave` | `/api/v1/erp/leave/...` |
| Inventory / stock | `products.cycom.inventory` | `/api/v1/erp/inventory/...` |
| Procurement / purchasing | `products.cycom.procurement` | `/api/v1/erp/procurement/...` |
| Fleet / vehicle maintenance | `products.cycom.fleet` | `/api/v1/erp/fleet/...` |
| Accounting / GL | `products.cycom.accounting` | `/api/v1/erp/accounting/...` |
| AR/AP, vendor invoices | `products.cycom.ar_ap` | `/api/v1/erp/ar-ap/...` |
| Maintenance tickets | `products.cycom.maintenance` | `/api/v1/erp/maintenance/...` |
| Helpdesk | `products.cycom.helpdesk` | `/api/v1/erp/helpdesk/...` |
| Documents / DMS | `products.cycom.documents` | `/api/v1/erp/documents/...` |
| Expenses | `products.cycom.expenses` | `/api/v1/erp/expenses/...` |

## What CyED builds itself (education-specific, not in CyCom)
SIS, curriculum (ACARA), timetable, attendance, gradebook, **report cards**,
admissions, LMS, wellbeing (+ sentiment), **transport (school trips/zones/RFID/GPS)**,
**tuition billing & installments**, library, **health/clinic**, events/excursions,
visitor management, and all the education AI (tutor, Socratic, teacher tools,
at-risk, fee-risk, substitution).

> Note on overlap: CyED's `transport` is *school* transport (door-to-door trips,
> zone fares, RFID/GPS) — distinct from CyCom `fleet` (general vehicle asset +
> maintenance). CyED `billing` is *tuition/installments*; CyCom `accounting/ar_ap`
> is the general ledger the school's finance office runs.

## Deployment
Both apps share the same PostgreSQL cluster + CyIdentity realm. Set
`CYED_CYCOM_URL` to CyCom's ingress; the shared JWT means a staff member's token
is accepted by both. No data duplication.
