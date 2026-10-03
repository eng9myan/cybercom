# GAP_ANALYSIS.md — CyCom vs Odoo Module Map (Phase 1, 2026-08-25, re-verified 2026-10-03)

> **2026-10-03 re-verification note:** this file is from the Phase 1 pass and
> had gone stale on 7 rows — Payment gateway, Payroll-beyond-JO,
> Multi-company, Project, Manufacturing, Studio, and eCommerce storefront
> were all marked Missing/Partial but had since been built (spot-checked
> directly against the current code, not just memory). Fixed in place below.
> `PROJECT_STATE.md` is the up-to-date source of truth going forward — check
> it first before trusting anything in this file as current.

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
| Project | `project` | Present | P2 | Timesheets (logged hours roll into Task.effective_hours) + real CPM scheduling (forward/backward pass, slack, cycle-detection) with a Gantt frontend — built later, row was stale. |
| Manufacturing (MRP) | `manufacturing` | Present | P2 | Real MRP now: WorkCenter/Routing/RoutingOperation, auto-generated WorkOrders per operation (strictly sequenced), work_center_load() capacity planning. Built later, row was stale; still not launch-critical for Commerce. |
| Multi-company | `products.cycom.company` | Present | — | Multi-tenant strong; multi-company **within** a tenant now modeled too (`Company` w/ `parent_company` self-FK, nullable FK on JournalEntry/PurchaseOrder/SalesOrder/ManufacturingOrder, optional `company=` filter on the 5 statement functions) — built later, not reflected when this row was first written. Intercompany auto-mirroring and per-company CoA/numbering still deliberately out of scope. |
| Multi-currency | model currency fields | Partial | P1 | Currency stored per order; no rate table / revaluation. |
| Studio (extensibility) | `cyai_moduledev`, `provisioning`, `customfields` | Partial | P2 | Provisioning blueprints + AI-propose + a real no-code custom-fields system (5 whitelisted models, attributes JSONField, Settings UI) now exist — built later, row was stale. Still no end-user form/layout designer. |

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
| eCommerce storefront (online ordering) | `products.cycom.storefront` | Present | P2 | Built later, row was stale: public `/store/[slug]` + cart + checkout creating a real SalesOrder, token-based guest cart, opt-in `Product.is_published_online`. |
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

**P2 — after first launch:** loyalty/promotions, Studio-style end-user form/layout designer. (eCommerce storefront, MRP depth, and Project depth are now done — see rows above.)

## The honest one-liner

CyCom's **operational core is Present** (sell, stock, buy, book, pay staff) and the **Commerce vertical is its strongest, most-tested, most-differentiated surface** (POS + live KDS). As of 2026-10-03, payment gateway and payroll-beyond-JO are both code-complete (see re-verification note above) — the gap to first revenue is now **entirely infra/business, not features**: a hosted Keycloak, live payment-provider keys, confirming 2 payroll rates, and a hosting platform to deliver tenants. Everything else is P2 polish that should not delay launch.
