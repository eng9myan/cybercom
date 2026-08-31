# GAP_ANALYSIS.md — CyCom vs Odoo Module Map (Phase 1, 2026-08-25)

> Launch product = **CyCom** (Commerce/Retail-first), per `MARKET_READINESS.md`.
> Scope here is CyCom only. CyShop is folding in (its unique parts already ported);
> CyMed gets its own gap pass before it earns a launch date.
> Status: **Present** (works + tested) / **Partial** (exists, incomplete) / **Missing**.
> Priority: **P0** blocks the first launch · **P1** needed for CyCom's commercial launch ·
> **P2** parity polish, after first launch.

## Odoo core suite → CyCom

| Odoo module | CyCom app(s) | Status | Priority | Notes |
|---|---|---|---|---|
| CRM | `crm` | Partial | P1 | Lead only; no Opportunity/pipeline/activities. Thin. |
| Sales | `sales` | Present | — | SalesOrder + lines, quotations, retail/wholesale, invoice bridge. Verified. |
| Inventory | `inventory` | Present | — | Warehouse, Product, StockItem (valuation), StockMove, InternalOrder. Core solid. |
| Purchase | `procurement` | Present | — | PurchaseRequest→PO→GoodsReceipt. Approval workflow present. |
| Accounting | `accounting` + `ar_ap` | Present (core) | P1 | Real journal posting, AR/AP, invoices, partners. **Missing**: tax reports, P&L/BS statements, bank recon. |
| HR | `hr` + `leave` + `recruitment` | Present (core) | — | Employee, Contract, Leave, Applicant. |
| Payroll | `payroll` | Partial | P1 | PayrollRun, Payslip, attendance, JO social-security. Only JO localized; other countries missing. |
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
| **Payment gateway** | — | **Missing** | **P0** | `register` only raises a bank-transfer-pending invoice. No card capture. Blocks paid self-serve. |
| eCommerce storefront (online ordering) | — | Missing | P2 | POS-first launch doesn't require it; needed for omnichannel later. |
| Loyalty / promotions | — | Missing | P2 | |

## Cross-cutting

| Concern | Status | Priority | Notes |
|---|---|---|---|
| Multi-tenant isolation | Present | — | Enforced at queryset (`TenantScopedModelViewSet`); RLS path exists. |
| Auth — production (Keycloak/OIDC) | Present | **P0** | Real, but must be stood up on a real box to run at all. |
| Auth — demo (dev-auth shim) | Present | — | Works without Keycloak; demo/dev only. |
| RTL / Arabic bilingual | Partial | P1 | Not audited; prompt marks it a hard requirement. |
| Hosting / Odoo.sh-equivalent platform | Missing | P1 | No git-branch envs / one-click tenant provisioning platform yet. |
| Automated tests | Partial | P1 | Strong on the apps built this session (catalog/pos/sales); coverage uneven elsewhere. |

## Launch-critical backlog (ordered)

**P0 — before a first paying customer can self-serve:**
1. **Keycloak on a real box** — unblocks signup/login end-to-end. (Or: hand-provision the first customer's tenant and defer.)
2. **Payment gateway** — Stripe + regional (HyperPay/PayTabs for JO/SA/AE) on the `register` flow. (Or: manual invoicing for the first hand-held deal.)

**P1 — for a credible commercial CyCom (Commerce):**
3. Hosting/provisioning platform (git-branch envs, one-click tenant instance) — prompt §8.
4. Accounting reports (P&L, Balance Sheet, tax return) + multi-currency rate table.
5. CRM pipeline (Opportunity/stages/activities).
6. RTL/Arabic audit + fixes.
7. Payroll beyond JO (SA/AE localizations).

**P2 — after first launch:** eCommerce storefront, loyalty/promotions, MRP depth, Project depth, Studio-style field designer.

## The honest one-liner

CyCom's **operational core is Present** (sell, stock, buy, book, pay staff) and the **Commerce vertical is its strongest, most-tested, most-differentiated surface** (POS + live KDS). The gap to first revenue is **not features** — it's **two enablers (Keycloak-hosted + payments)** and a **hosting platform** to deliver tenants. Everything else is P2 polish that should not delay launch.
