# GAP_ANALYSIS.md — CyCom vs Odoo Module Map (Phase 1, 2026-08-25, re-verified 2026-10-03)

> **2026-10-03 re-verification note:** Payment gateway and Payroll-beyond-JO
> below were stale — both were built in later sessions. `PROJECT_STATE.md` is
> the up-to-date source of truth; this file's other rows were spot-checked
> against current code and still hold, but check `PROJECT_STATE.md` first
> before trusting anything here as current.

> Launch product = **CyCom** (Commerce/Retail-first), per `MARKET_READINESS.md`.
> Scope here is CyCom only. CyShop is folding in (its unique parts already ported);
> CyMed gets its own gap pass before it earns a launch date.
> Status: **Present** (works + tested) / **Partial** (exists, incomplete) / **Missing**.
> Priority: **P0** blocks the first launch · **P1** needed for CyCom's commercial launch ·
> **P2** parity polish, after first launch.

## Odoo core suite → CyCom

| Odoo module | CyCom app(s) | Status | Priority | Notes |
|---|---|---|---|---|
| CRM | `crm` | Present | — | Staged pipeline (Lead.stage, funnel/weighted-value aggregation) + Activity log, tested, Kanban UI. Multi-currency rate table (row 12) is separate. |
| Sales | `sales` | Present | — | SalesOrder + lines, quotations, retail/wholesale, invoice bridge. Verified. |
| Inventory | `inventory` | Present | — | Warehouse, Product, StockItem (valuation), StockMove, InternalOrder. Core solid. |
| Purchase | `procurement` | Present | — | PurchaseRequest→PO→GoodsReceipt. Approval workflow present. |
| Accounting | `accounting` + `ar_ap` | Present | — | Real journal posting, AR/AP, invoices, partners, trial balance/P&L/balance sheet/VAT return, bank reconciliation. All tested. No frontend statements viewer yet. |
| HR | `hr` + `leave` + `recruitment` | Present (core) | — | Employee, Contract, Leave, Applicant. |
| Payroll | `payroll` | Present | — | PayrollRun, Payslip, attendance, JO + SA GOSI + UAE gratuity/GPSSA, country dispatcher, 11 tests (done — see PROJECT_STATE.md). 2 rates (SA scheme choice, UAE national %) need business confirmation, not code. |
| Project | `project` | Partial | P2 | Basic; no Gantt/timesheet depth. |
| Manufacturing (MRP) | `manufacturing` | Partial | P2 | BOM/work-order basics; not launch-critical for Commerce. |
| Multi-company | `platform/tenant` | Partial | P1 | Multi-**tenant** strong; multi-company **within** a tenant not modeled (dropped Company FK). Branches TBD. |
| Multi-currency | model currency fields | Partial | P1 | Currency stored per order; no rate table / revaluation. |
| Studio (extensibility) | `cyai_moduledev`, `provisioning` | Partial | P2 | Provisioning blueprints + AI-propose exist; no end-user field/form designer. |

## Commerce-vertical (CyCom-first launch surface)

| Capability | CyCom app | Status | Priority | Notes |
|---|---|---|---|---|
| Product catalog (variants/kits/categories) | `catalog` | Present | — | Ported from CyShop, tested. |
| POS (sessions, orders, payments) | `pos` | Present | — | Strong; incl. layaway, discount-approval, journal posting. |
| **KDS / kitchen display** | `pos` (Device/kitchen_status) | Present | — | Built + live-verified this session. Differentiator vs Odoo. |
| Receipts | `pos.PosReceipt` | Present | — | |
| Self-serve onboarding | `cycom-erp` `/onboarding`, `/setup` | Present | — | 10-step provisioning wizard + Commerce quick-setup. |
| Self-serve signup (tenant register) | `platform/tenant` + `/signup` | Partial | **P0** | Wired end-to-end **but** realm provisioning needs Keycloak (fails on no-Docker). |
| **Payment gateway** | `platform/tenant/payments.py` | Present | — | HyperPay (create_checkout + AES-256-GCM webhook decrypt + verify) and Stripe both fully implemented, plus manual/fake providers. Frontend checkout render in `/signup`. Needs live HyperPay merchant keys to actually charge a card — that's an account/infra step, not a code gap. |
| eCommerce storefront (online ordering) | — | Missing | P2 | POS-first launch doesn't require it; needed for omnichannel later. |
| Loyalty / promotions | — | Missing | P2 | |

## Cross-cutting

| Concern | Status | Priority | Notes |
|---|---|---|---|
| Multi-tenant isolation | Present | — | Enforced at queryset (`TenantScopedModelViewSet`); RLS path exists. |
| Auth — production (Keycloak/OIDC) | Present | **P0** | Real, but must be stood up on a real box to run at all. |
| Auth — demo (dev-auth shim) | Present | — | Works without Keycloak; demo/dev only. |
| RTL / Arabic bilingual | Present (core) | — | Large sweep done across 30+ batches in later sessions (RTL arrows, logical CSS properties, i18n key parity, locale cookie SSR). Not re-verified in this pass — check for drift before citing as finished. |
| Hosting / Odoo.sh-equivalent platform | Missing | P1 | No git-branch envs / one-click tenant provisioning platform yet. |
| Automated tests | Partial | P1 | Strong on the apps built this session (catalog/pos/sales); coverage uneven elsewhere. |

## Launch-critical backlog (ordered)

**P0 — before a first paying customer can self-serve:**
1. **Keycloak on a real box** — unblocks signup/login end-to-end. (Or: hand-provision the first customer's tenant and defer.)
2. ~~Payment gateway~~ — **done**: Stripe + HyperPay (the regional pick for JO/SA/AE)
   both fully implemented on the `register` flow, plus manual/fake providers.
   Remaining is an account step (live HyperPay merchant keys), not code.

**P1 — for a credible commercial CyCom (Commerce):**
3. Hosting/provisioning platform (git-branch envs, one-click tenant instance) — prompt §8.
4. ~~Accounting reports~~ — **done 2026-09-19**: trial balance/P&L/balance sheet/VAT return
   already existed (now test-covered) and bank reconciliation was built and tested
   (`products/cycom/accounting/{reports,bank_reconciliation}.py`). Still open: multi-currency
   rate table / revaluation, and a frontend page to actually view these statements (the
   `/reports/*` endpoints have no UI consumer yet).
5. ~~CRM pipeline~~ — **done 2026-09-19**: the backend already had a full staged pipeline
   (Lead.stage, funnel/weighted-value aggregation, Activity log) and a Kanban frontend —
   the real bug was the Kanban's stage-move buttons never persisting `stage` to the backend
   (fixed in `cycom-erp/app/crm/page.tsx`).
6. ~~RTL/Arabic audit + fixes~~ — **largely done** across later sessions (30+
   batches); not re-verified in this pass, see the Cross-cutting row above.
7. ~~Payroll beyond JO~~ — **done**: SA GOSI + UAE gratuity/GPSSA + country
   dispatcher, 11 tests. 2 rates still need business confirmation (SA scheme
   choice, UAE national %) — not a code gap.

**P2 — after first launch:** eCommerce storefront, loyalty/promotions, MRP depth, Project depth, Studio-style field designer.

## The honest one-liner

CyCom's **operational core is Present** (sell, stock, buy, book, pay staff) and the **Commerce vertical is its strongest, most-tested, most-differentiated surface** (POS + live KDS). As of 2026-10-03, payment gateway and payroll-beyond-JO are both code-complete (see re-verification note above) — the gap to first revenue is now **entirely infra/business, not features**: a hosted Keycloak, live payment-provider keys, confirming 2 payroll rates, and a hosting platform to deliver tenants. Everything else is P2 polish that should not delay launch.
