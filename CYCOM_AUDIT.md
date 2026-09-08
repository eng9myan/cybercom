# CyCom ERP — Full System Audit

**Engagement:** Multi-disciplinary functional / workflow / design / localization audit
**Method:** Live stack (Django `:8090` + Next `:7000`, no-Docker dev-auth), seeded dev tenant `11111111-…`, provisioned as *Amman Builders Co.* (JO / construction / medium). API-driven business-cycle testing + code review + test suites. Live in-browser UI/design pass pending browser connection.
**Audit run:** 2026-09-08 (in progress)
**Repo state:** `D:\cybercom` @ `4dcc3af` (branch `develop`)

---

## STATUS: v1 COMPLETE + P0 FIXES APPLIED & VERIFIED (2026-09-08)

**P0 remediation done** (live-verified on the fresh-provisioned dev tenant; 146/146 `products/cycom` tests still pass):

| P0 | Fix | Verified |
|---|---|---|
| **A-1** dup number → 500 | `InvoiceSerializer.validate()` pre-checks `(tenant_id, number)` → clean 400 field error | ✅ 400 "already exists for this tenant" |
| **A-2** negative qty accepted | `InvoiceLineSerializer.validate_quantity/unit_price` reject `<= 0` / `< 0` | ✅ 400 "must be greater than zero" |
| **A-3** post to header account | `Account.is_postable` (auto-false for accounts with children; data migration backfills) + hard reject in `accounting.services.post_journal_entry` (the one GL choke point → covers ar_ap, pos, payroll, inventory, expenses) | ✅ 400 "Cannot post to group/header account(s): 4000" |
| **A-5** draft totals 0.00 | `InvoiceSerializer.create()` computes header totals from lines on create | ✅ draft shows 1160.00 |
| **C-1** no credit-note type | `Invoice.invoice_type` += `customer_credit_note` / `vendor_credit_note` + `reverses` FK; `post_invoice` posts the reversed GL entry; over-credit blocked; JoFotara clearance extended to customer credit notes | ✅ CN posts reversed entry (Dr Revenue/Dr VAT/Cr AR); over-credit → 400 |
| **HR-2** 3-way match advisory-only | `post_invoice` now runs `three_way_match` for PO-linked vendor bills and **blocks** out-of-tolerance bills; `override_match=true` (admin role) to force | ✅ over-billed PO bill → 400; posts after goods receipt |
| _bonus_ **A-6** GST/VAT terminology | JO CoA pack: "Input GST"→"Input VAT", "Output GST"→"Output VAT", tax name → "VAT" | ✅ |
| _bonus_ **A-7** duplicate CoA accounts | `seed_demo_commerce` now targets the JO chart's **leaf** codes (1110/4100/5100) instead of creating flat duplicates of the header codes | ✅ `seed_demo_commerce` creates 0 new accounts |

Files changed: `products/cycom/accounting/{models,services}.py` (+migration `0003`), `products/cycom/ar_ap/{models,serializers,views}.py` (+migration `0010`), `platform/provisioning/packs/countries/JO.json`, `platform/provisioning/management/commands/seed_demo_commerce.py`.

Remaining CyCom P0 (minor): extend `seed_demo_commerce` to check orders out (demo polish); `StockMove` serializer `quantity > 0` validation.

---

## STATUS: v1 (audit) — REVISED (2 findings corrected after deeper testing; see S-1, I-1)

**Revision note:** S-1 (POS→GL) and I-1 (negative stock) were mis-filed as Critical/High in the first pass — both were tested against the *seed state* rather than the live posting path. Re-verified: POS checkout posts GL + COGS + goods-issue atomically; `apply_stock_move` blocks negative stock. Both downgraded to Low. **Revised count: 0 Critical, 5 High.**

| Persona | Status |
|---|---|
| Accounting & Finance | done — A-1..A-8 (3 High: A-1, A-2, A-3) |
| Inventory & Supply Chain | done — I-1..I-3 (I-1 corrected → Low) |
| HR & Payroll | done — HR-1..HR-8 (1 High: HR-2) |
| Sales, CRM & POS | done — S-1 (corrected → Low), S-2..S-4 |
| Procurement | done — HR-2..HR-4 |
| Compliance & E-Invoicing | done (code+API) — C-1..C-3; XAdES/PIH-continuity/AR-PDF need live pass |
| Executive / CEO Dashboards | done — E-1 |
| IT Administration & Security | done (live) — IT-1..IT-3; **prod-path RBAC / tenant-isolation / audit-chain / secrets code review still OUTSTANDING** (dev-auth = AllowAny blocks live testing) |
| Bilingual Localization (EN/AR) | done (source) — L-1..L-4; UI-leakage check needs browser |
| UX/UI & Brand | source-only — U-1; **full visual/click-through pass needs Chrome extension** |
| Prospective Buyer verdict | **done** (below) |

_Scan window: live stack — Django `:8090` (`core.settings_dev`, dev-auth), Next `:7000`, dev tenant provisioned as Amman Builders Co. (JO/construction) + `seed_demo_commerce` + `seed_demo_business`. API-driven business-cycle testing + code review + `products/cycom` test suite (146 pass, `core.settings_test`)._

---

## SURFACE MAP

### Frontend routes (84 pages, `cycom/cycom-erp/app`)
accounting, accounting/import, accounting/journals, accounting/reconciliation, approvals, attendance, attendance/devices, attendance/overtime, attendance/schedule, crm, dashboard, discuss, documents, expenses, fleet, fleet/vehicles/[id], helpdesk, hr, hr/departments, hr/documents, hr/employees, hr/employees/import, hr/insurance, hr/requests, inventory, inventory/branch-orders, inventory/branch-orders/[id]/receive, inventory/import, inventory/reports, inventory/transfers, inventory/warehouse-requests, kds, knowledge, login, maintenance, marketing, onboarding, payroll, payroll/deductions, payroll/overtime, payroll/payslips, planning, plm, portal, portal/checkin, portal/leaves, portal/payslips, pos, pos/orders, pos/reports, pos/session, project, purchase, purchase/vendors, purchase/vendors/[id], purchase/vendors/new, quality, recruitment, sales, sales/approvals, sales/orders, settings, settings/modules, settings/security, settings/tax, settings/workflows, setup, setup/coa, setup/company, setup/hr, setup/manufacturing, setup/payroll, setup/permissions, setup/pos, setup/procurement, setup/sales, setup/warehouse, sign, sign/public/[token], sign/requests, sign/templates, signup, subscriptions

### Backend API (~48 app groups under `/api/v1/`)
access, accounting (+reports: trial-balance, profit-and-loss, balance-sheet, vat-return), ai, ar-ap (invoices +post +three-way-match, partners +submit/approve/reject, payments +post), audit (large: events, chains, evidence, legal-holds, retention, compliance/*), calendar, catalog, crm, discuss, documents, einvoicing, equity, esg, expenses, field-service, fleet, helpdesk, hr, inventory (warehouses, products, stock-items, moves, internal-orders), knowledge, leave, localization, logistics, maintenance, manufacturing, marketing, notes, payroll, planning, plm, pos (sessions, orders, devices, receipts), procurement (requests, orders), project, provisioning (country-packs, department-packs, industry-templates, blueprints +provision, config-parameters, ai-propose), quality, recruitment, sales (orders), scheduler, subscriptions, todo, tenants (register, demo, pricing, payments)

---

## FINDINGS

_Severity: Critical / High / Medium / Low. Format: module — repro — expected vs actual — fix — persona._

### Accounting & Finance

**A-1 (High) — Duplicate invoice number → HTTP 500 IntegrityError.**
Repro: `POST /api/v1/ar-ap/invoices/` twice with same `number` + `invoice_type`. Expected: 400 "invoice number already exists". Actual: uncaught `IntegrityError`, 500, Django debug page (stack trace leak under DEBUG). A user double-clicking Save or retrying a timed-out request hits this. Fix: serializer `UniqueTogetherValidator` on `(tenant_id, number, invoice_type)`; friendly 400.
Persona: Accounting.

**A-2 (High) — Negative quantity accepted on invoice line.**
Repro: create customer invoice line `quantity: -5, unit_price: 100` → 201, `subtotal: -500`, `tax_amount: -80`. Expected: rejected; reversals go through a credit-note flow with its own numbering/approval. Actual: silent negative-revenue invoice — an uncontrolled back-door credit note. Fix: validate `quantity > 0`, `unit_price >= 0` on `InvoiceLine`; add a real credit-note document type.
Persona: Accounting.

**A-3 (High) — Invoice/JE lines can post to header (roll-up) accounts.**
Repro: invoice line `account = 1100 Current Assets` (a parent/summary account) → 201, will post. Expected: only leaf/postable accounts accept entries. Actual: no `is_postable`/`is_group` guard → corrupts trial-balance hierarchy and financial statements. Fix: `Account.is_postable` flag, default false for accounts with children; enforce on JournalLine + invoice line + all posting paths.
Persona: Accounting.

**A-4 (Medium) — Invoice number is required free-text with no auto-sequence.**
`number` REQ, manually typed. No per-tenant/per-type gapless sequence. JoFotara/ISTD requires sequential numbering per document type; manual entry guarantees gaps/dupes (and A-1). Fix: auto-generate from a `DocumentSequence`; manual override gated by permission.
Persona: Accounting, Compliance.

**A-5 (Medium) — Draft invoice header totals show 0.00 while lines carry real amounts.**
Repro: create invoice with one line (`subtotal 1000 / tax 160`); read it back in `draft` → `amount_subtotal/amount_tax/amount_total = 0.00`. Totals only populate on `post`. A reviewer/approver sees a 0.00 invoice. Fix: recompute header totals from lines on every write.
Persona: Accounting, CEO.

**A-6 (Medium) — Tax terminology: CoA mixes "GST" and "VAT".**
`1150 Sales Tax Receivable (Input GST)` vs `2120 Output VAT`. Jordan (and Gulf) use "VAT". A local accountant flags "GST" as wrong on sight. Fix: rename `1150` → "Input VAT"; sweep templates for "GST".
Persona: Accounting, Localization.

**A-7 (Low) — Duplicate account names in seeded JO CoA.**
`1000 Cash on Hand` and `1110 Cash on Hand` both present, both `asset`. Ambiguous which to use for cash receipts. Fix: dedupe the construction/JO CoA pack; one cash-on-hand + one bank parent.
Persona: Accounting.

**A-8 (Low) — e-invoice `status: rejected` set silently on post with no real authority connection.**
Post → `einvoice_status: "rejected"` (no JoFotara endpoint in dev). Model should distinguish `not_submitted` / `queued` / `rejected`. As-is a user can't tell a real rejection from "offline". Fix: default `not_submitted`; only set `rejected` on an actual authority response.
Persona: Compliance.

_Verified-good in this cycle: posting a customer invoice creates a correctly balanced journal entry (AR 1160 Dr / Revenue 1000 Cr / Output VAT 160 Cr); trial balance ties (1160 = 1160, `balanced: true`); JoFotara e-invoice envelope (UUID, ICV counter, PIH hash-chain, document hash) is generated automatically on post._

### Inventory & Supply Chain

**I-1 (Low) — [CORRECTED — was mis-filed High] `apply_stock_move` blocks negative stock; only the raw draft-create is unvalidated.**
Initial report was wrong. Re-verified: `apply_stock_move()` raises `ValidationError("Cannot issue 2.0000: only 0 on hand.")` for `issue` and `transfer` beyond on-hand — every real posting path (POS checkout, manual issue, transfer) is gated. The gap: `POST /api/v1/inventory/moves/` creates a `StockMove` row with `status: draft` and no serializer validation, so an absurd quantity is *accepted into a draft* — but the draft is inert (no stock/GL effect) until something applies it, and apply-time re-validates. Fix (minor): add `quantity > 0` + availability validation to the move serializer so drafts can't hold impossible values; no "allow negative" flag exists, which is fine (negative stock is simply blocked).
Persona: Inventory.

**I-2 (Medium) — Inventory move `unit_cost` optional and null on issue; valuation impact unclear.**
`issue` move created with `unit_cost: null`, `journal_entry: null`, stays `draft`. No visible costing method (FIFO/AVCO) selection; `average_cost` on stock-items is 0.0000 for several seeded products. Fix: enforce costing method per product/tenant; compute issue cost from AVCO/FIFO; never allow a valued move with null cost.
Persona: Inventory, Accounting.

**I-3 (Medium) — `date` required on every move with no default to today; `move_type` has no "in/out" synonyms.**
Minor UX friction; enum is `receipt/issue/transfer/adjustment` (fine) but errors are cryptic (`"out" is not a valid choice`). Fix: default date; clearer validation messaging.
Persona: Inventory.

### Sales, CRM & POS

**S-1 (Low) — [CORRECTED — was mis-filed Critical] POS checkout posts to the GL correctly; the seed just doesn't check orders out.**
Initial report was wrong. Re-verified live: create POS order → `POST /pos/orders/{id}/checkout/` → status `paid` and **two balanced journal entries post atomically**: (1) Cash Dr / Revenue Cr / Output VAT Cr, (2) COGS Dr / Inventory Cr; stock decrements; trial balance ties; revenue flows to the P&L. `checkout_order()` (`pos/services.py`) is well built — atomic, weighted-average costing shared with manual issues, blocks insufficient stock, handles layaway.
Real (minor) gaps: (a) `seed_demo_commerce` creates POS orders in `draft` and never checks them out, so a fresh demo/audit sees unposted orders — **demo-data quality, not a product bug**; (b) served KDS tickets do not auto-progress toward checkout — no lifecycle auto-completion; (c) see S-2.
Persona: Sales, Inventory.

**S-2 (High) — POS order creation demands GL account IDs (`cash_account`, `revenue_account`, `cogs_account`) and `order_number` on every request.**
Repro: `POST /api/v1/pos/orders/` → 400 requiring those four fields. Expected: accounts come from POS/session/store config; number auto-sequences. Actual: caller must supply chart-of-accounts UUIDs per sale — unusable from a real POS till, and a numbering-collision risk. Fix: resolve accounts from POS config; auto-number.
Persona: Sales, IT.

**S-3 (Medium) — Two parallel product models: `catalog.Product` (CyShop port) and `inventory.Product`.**
POS order lines reject a `catalog.Product` id ("object does not exist") — they want `inventory.Product`. Catalog has 19 products, inventory has 25, overlapping. Unclear which is authoritative; risk of price/stock drift. Fix: one product master; catalog = presentation layer over it, or migrate fully.
Persona: Sales, Inventory, Buyer.

**S-4 (Medium) — Order-to-cash skips delivery/goods-issue.**
`sales/orders/{id}/confirm/` → `create-invoice/` produces an AR invoice directly; no delivery step, no stock movement, even for stockable lines. Seeded SO lines have `product: null` so nothing to ship, but the flow offers no delivery stage at all. Fix: add a delivery/fulfilment step that issues stock and feeds COGS before or alongside invoicing.
Persona: Sales, Inventory.

_Verified-good: `sales/orders/{id}/confirm/` then `create-invoice/` works cleanly — order → confirmed → invoiced, AR invoice created and linked._

### HR & Payroll

**HR-1 (Medium) — Payroll run requires GL account IDs (`salary_expense_account`, `salary_payable_account`, `deduction_recovery_account`) passed in the POST body.**
Same anti-pattern as S-2: posting accounts should be tenant payroll config, not hand-entered per run. Fix: default from config; allow override with permission.
Persona: HR, Accounting.

**HR-2 (High) — 3-way match is advisory-only and enforces nothing.**
`ar-ap/invoices/{id}/three-way-match/` is a **GET** report. `post_invoice()` never calls it. Repro: create a vendor bill with `purchase_order` set for 50 units when the PO ordered 10 / received 0 → posts to AP with no block or warning. Expected: posting a PO-linked bill outside tolerance is blocked or needs override. Actual: no enforcement anywhere. (Contradicts prior internal notes claiming "blocks billing above received".) Fix: call the match in `post_invoice` for PO-linked bills; block/΄require-approve outside `TOLERANCE`.
Persona: Procurement, Accounting.

**HR-3 (Medium) — Vendor-bill ↔ PO link is unvalidated.**
`purchase_order` on an invoice is a free FK — not checked that the vendor matches the PO vendor, currency matches, or the PO belongs to the tenant's approved set. Fix: validate on write.
Persona: Procurement.

**HR-4 (Medium) — Provisioned approval matrix (ApprovalPolicy/ApprovalTier) is not enforced on approve actions.**
Provisioning generates value-based approval tiers per industry/size (a marketed feature). But `PurchaseOrderViewSet.approve` / `InvoiceViewSet.approve` only check `IsPlatformAdmin` (role in {platform_admin, cyidentity_admin, tenant_admin}). No amount thresholds, no Finance/Procurement Manager role, no multi-step approval. Fix: wire approve actions to the ApprovalPolicy engine; add finance/procurement approver roles.
Persona: Procurement, Accounting, CEO.

**HR-5 (Medium) — Payroll run requires GL account IDs in the POST body (see HR-1); after `post`, run's `journal_entry` stays null in the response.**
Payslip generation works (12 payslips, SS employee 60.00 / employer 114.00 on gross 800 = 7.5% / 14.25% ✓). But `POST runs/{id}/post/` → 200 while the run object still shows `journal_entry: null` — unclear whether the salary JE actually posted. Fix: confirm/return the JE; surface it on the run.
Persona: HR, Accounting.

**HR-6 (Medium) — Jordan income-tax model likely incomplete vs current ISTD rules.**
`payroll/rules.py`: taxes **basic salary only** (not gross taxable employment income); personal exemption is 9,000 / 18,000 (married sole-earner) with **no** JD 3,000 additional deductions (medical/education/rent/murabaha) and **no** national contribution tax. Bands 5/10/15/20/25% look right. If "basic-only" is a deliberate client choice, document it; otherwise several employees' withholding will be wrong. Fix: confirm against 2026 ISTD guidance; make taxable-base and additional deductions configurable.
Persona: HR, Compliance.

**HR-7 (Medium) — Social-security base = gross (incl. allowances), uncapped.**
`social_security()` applies 7.5% / 14.25% to full gross. Jordan SSC has a defined subject-wage (basic + fixed allowances) and a monthly ceiling. Fix: configurable subject-wage components + SSC ceiling cap.
Persona: HR, Compliance.

**HR-8 (Low) — Payslip is thin.**
No payslip number, no tax breakdown lines, no employer-cost total, no amount-in-words, no bilingual layout. Fix: proper payslip document.
Persona: HR.

_Verified-good: SS rates correct (7.5% / 14.25%); payment posting has solid guards (no double-post, invoice-must-be-posted, payment ≤ amount due); PO `receive` action exists and posts real inventory receipt StockMoves; `post_invoice` is concurrency-safe (row_version CAS, JE+flip atomic)._

### IT Administration & Security

**IT-1 (Medium) — `page_size` query param ignored; hard page cap ~25.**
`GET /api/v1/accounting/accounts/?page_size=200` returns 25 with a `next` link. No way to raise page size → bulk export / integration sync requires many round-trips. Fix: honour `page_size` up to a sane max (e.g. 1000).
Persona: IT, Integrations.

**IT-2 (Medium) — Seeded JO construction CoA has duplicate account names.**
`1000` & `1110` "Cash on Hand"; `4000` & `4100` "Sales Revenue"; `5000` & `5100` "Cost of Goods Sold". Shipped template, every JO construction tenant inherits this. Fix: clean the pack.
Persona: Accounting, Buyer.

**IT-3 (Low) — Money fields inconsistently typed in API (`amount_total` float on PO vs string elsewhere).**
Fix: serialize all monetary values consistently (string decimals).
Persona: IT, Integrations.

_(Deeper security review — tenant isolation, audit-log integrity, RBAC in the real Keycloak path, secrets, rate-limiting — done by code review in a later section; the live stack runs dev-auth = AllowAny so runtime RBAC can't be exercised here.)_

### Bilingual Localization (EN / AR)

**L-1 (Medium) — No i18n framework; custom string lookup with no locale-aware formatting.**
`lib/i18n` is a hand-rolled dotted-key lookup (deliberately not next-intl, documented). `t(key, vars)` does string interpolation only — **no `Intl.NumberFormat` / currency / date localization**. Arabic screens will still show Western digits, `1,234.56`, and en-US dates inside RTL text. Fix: add locale-aware formatters (numbers, currency, dates, Hijri option); route them through `t`.
Persona: Localization.

**L-2 (Medium) — String externalization is not enforced; coverage drift invisible.**
2,420 keys, EN/AR at exact parity (vitest key-parity test — good). But only ~92 of ~130 screen/component files import `useT`; the rest (~30%) have no translation calls → hardcoded English. The parity test checks EN==AR shape, not that UI strings are externalized at all. Fix: an extraction/lint step (or migrate to next-intl / i18next) that fails CI on literal JSX text.
Persona: Localization.

**L-3 (Medium) — CoA / backend seed data is English-only.**
Account names, role names, industry/department pack labels, seeded partner data are English strings in the DB. An Arabic-first tenant sees an English chart of accounts and English role names. `Partner.legal_name_ar` field exists (good) but packs don't populate Arabic. Fix: bilingual pack data; `name_ar` on Account/Role.
Persona: Localization, Accounting.

**L-4 (Low) — AR catalog carries its own disclaimer that professional review is still pending** ("Professional review still recommended before an Arabic-market GA"). Treat as an open pre-GA task, not done.
Persona: Localization.

_Verified-good: EN/AR key parity is test-enforced; sampled AR terminology is correct and professional ("ضريبة القيمة المضافة" = VAT, "تاريخ الاستحقاق" = due date); `dir=rtl` + `lang` driven from stored locale via `LocaleDirection`; missing keys render visibly (the key itself) in dev._

### UX / UI & Brand  _(source review; full visual pass pending browser)_

**U-1 (Medium) — Several screens still ship hardcoded mock data.**
`app/accounting/page.tsx` (reconciliation) has `INITIAL_BANK_LINES` / mock `JournalEntry` shapes alongside a real `useCycomList` call. Prior internal notes: ~65 of ~81 pages were mock; needs a full sweep. Fix: inventory every page, replace mock with backend calls or hide the page.
Persona: UX, Buyer.

### Executive / CEO Dashboards

**E-1 (Medium) — No consolidated dashboard / KPI / analytics API.**
`/api/v1/dashboard/`, `/reports/`, `/analytics/`, `/ai/reports/`, `/cyai/reports/` all 404. Only the three accounting statement endpoints + per-module lists exist. The `/dashboard` page must aggregate client-side (many round-trips; no multi-entity consolidation; no drill-down contract). Fix: a reporting/KPI service with period + entity params and drill-down links.
Persona: CEO.

---

## REASONS TO BUY (strengths)

- **Ready-ERP provisioning is real and fast.** One API call (`blueprints/{id}/provision/`) turns a blank tenant into a working JO construction company: 39-account CoA, 11 enabled modules, ~16 roles, approval tiers, JO localization + JoFotara wired — in ~1s. This is a genuine differentiator vs. Odoo's manual chart/localization setup.
- **Automatic e-invoicing on post.** Posting an AR invoice auto-builds the JoFotara envelope (UUID/ICV/PIH chain/hash) with no extra user step.
- **Balanced double-entry enforced** on the happy path; trial balance / P&L / balance sheet endpoints exist and tie (verified: TB 12,128 = 12,128 after invoice + payroll + procurement test data).
- **VAT return computes correctly** — output_tax 160.0 / input_tax 0 / net_payable 160.0 after one posted 16%-VAT invoice.
- Sales order → confirm → create-invoice works cleanly and links the invoice.
- Payment posting is well-guarded (no double-post, invoice-must-be-posted, payment ≤ amount due).
- PO `receive` (GRN) action posts real inventory receipt moves; `post_invoice` is concurrency-safe.

### Compliance & E-Invoicing (partial — code + API)

**C-1 (High) — No credit-note / debit-note document type.**
`/api/v1/ar-ap/credit-notes/`, `/accounting/credit-notes/`, `/sales/credit-notes/` all 404. The only way to reverse or reduce a posted invoice is A-2's negative-quantity invoice — which has no separate numbering, no approval, and no e-invoice credit-note handling. JoFotara requires credit notes as a distinct document referencing the original. Fix: a real CreditNote model + flow + JoFotara credit-note envelope.
Persona: Accounting, Compliance.

**C-2 (Medium) — VAT return has no filing period.**
`reports/vat-return/` returns `period: {from: null, to: null}` — an all-time figure. A VAT return must be for a declared ISTD filing period (monthly/quarterly), locked once filed. Fix: period params + a filed-return record.
Persona: Accounting, Compliance.

**C-3 (Medium) — No e-invoicing operations surface.**
JoFotara envelope (UUID / ICV / PIH chain / hash) is generated inside `post_invoice` — good — but there is no `/einvoicing/` API to see submission status, view a rejection reason, resubmit, or download the signed XML (XAdES). `einvoice_status` went to `rejected` on post with no way to act on it. Fix: an e-invoicing document/submission resource with status, response payload, retry, and signed-XML download.
Persona: Compliance, IT.

_(Not yet verified: XAdES-B signature validity against the ISTD schema, PIH chain continuity across many invoices, Arabic invoice PDF rendering — needs the browser/live-submission pass.)_

---

## EXECUTIVE SUMMARY

CyCom is a broad, genuinely capable **Django + Next.js ERP** with a real differentiator — the Ready-ERP provisioning engine turns a blank tenant into a configured JO company (39-account CoA, 11 modules, roles, approval tiers, JoFotara wiring) in about a second, and posting an invoice auto-builds the e-invoice envelope. The accounting core is sound on the happy path: double-entry is enforced, the trial balance / P&L / balance-sheet / VAT-return endpoints tie, payment posting is well-guarded.

The transaction engine is in better shape than the first pass suggested: **POS checkout posts GL + COGS + goods-issue atomically and blocks negative stock** (verified), double-entry goes through one choke point (`post_journal_entry`), the trial balance / P&L / balance-sheet / VAT-return tie. The audit found **no Critical**, but a cluster of **input-validation and financial-control holes** an accountant or auditor would stop on:

1. **The books can be corrupted through the front door**: duplicate invoice number → uncaught 500 debug page (A-1); negative-quantity invoice lines accepted as silent credit notes (A-2); journal/invoice lines postable to header/roll-up accounts (A-3); no credit-note document type at all (C-1).
2. **Financial controls that were built aren't wired**: 3-way match is a GET report that blocks nothing (HR-2); the value-based approval matrix that provisioning generates is not enforced on approve actions (HR-4).
3. **Numbering is manual everywhere** (invoices, POS orders, payroll runs) — gap/duplicate risk, against ISTD's gapless-sequence requirement (A-4).
4. **Config leaks into the API surface**: POS order creation and payroll runs demand chart-of-accounts UUIDs in every request body (S-2, HR-1).
5. **Localization has a framework gap** — no locale-aware number/currency/date formatting, ~30% of screens not externalized, English-only seed data (L-1–L-3).

None of these are architecture problems — they're validation, wiring, and lifecycle gaps. The remediation is a focused hardening pass, not a rebuild.

## PRIORITIZED FIX LIST — before selling CyCom

**Blockers (P0):**
1. **A-1** — duplicate document number → 400 with a field error, never a 500 / debug page.
2. **A-2 + C-1** — reject negative invoice-line quantities; add a real credit-note document type + flow + JoFotara credit-note envelope.
3. **A-3** — `Account.is_postable`; block entries against group/header accounts on every posting path.
4. **HR-2** — enforce 3-way match in `post_invoice` for PO-linked bills (block or require-override outside tolerance).
5. **S-1 (minor)** — extend `seed_demo_commerce` to check orders out so demos show posted sales; auto-progress served KDS tickets. **I-1 (minor)** — add `quantity > 0` validation to the StockMove serializer.

**High (P1):**
7. **A-4** — auto document numbering from per-tenant/per-type sequences.
8. **HR-4** — wire the ApprovalPolicy engine to PO / invoice approve actions; add finance/procurement approver roles.
9. **S-2 / HR-1** — resolve GL accounts from POS/payroll config, not request bodies.
10. **A-5** — recompute invoice header totals from lines on every write (drafts show real totals).
11. **HR-6 / HR-7** — confirm JO income-tax base + additional deductions and the SSC subject-wage/ceiling against current ISTD/SSC guidance.
12. **S-3** — one product master (resolve `catalog.Product` vs `inventory.Product`).
13. **L-1 / L-2** — locale-aware formatters; enforce string externalization (or move to next-intl / i18next).
14. **IT-1** — honour `page_size` for bulk export/integration.
15. Security code-review pass on the **prod Keycloak path**: tenant isolation on every viewset, audit-chain integrity, rate-limiting, secrets — not exercisable under dev-auth.

**Medium (P2):**
16. **S-4** — add a delivery/goods-issue stage to order-to-cash.
17. **C-2 / C-3** — VAT return filing periods; an e-invoicing operations resource (status / rejection / resubmit / signed-XML download).
18. **A-6 / A-7 / IT-2** — fix the JO CoA pack (GST→VAT, dedupe account names).
19. **E-1** — a reporting/KPI service for the CEO dashboard with period + entity params and drill-down.
20. **L-3** — bilingual pack/seed data.
21. **U-1** — sweep every frontend page; replace remaining mock data with backend calls.
22. Full **in-browser UX/UI + bilingual pass** (blocked this run — Chrome extension not connected).

## BUYER VERDICT (skeptical SMB owner comparing against Odoo)

**Would I buy CyCom today? Not quite — but it's closer than I expected, and the setup experience beats Odoo's.** The Ready-ERP wizard genuinely does in seconds what takes an Odoo consultant days (chart of accounts, localization, roles, approvals, e-invoicing). POS + KDS are real and — checked properly — a till sale does post to the ledger, VAT and COGS included. That's a credible pitch.

What stops me signing now: I ran a few normal transactions and hit a server error just by re-entering an invoice number, and watched a negative-quantity invoice save without a warning. For software I'm trusting with my books and my tax filing, that's what my accountant calls a red flag — small to fix, but it has to be fixed before I hand over the ledger.

**What flips me to yes:** input validation that refuses to corrupt the books (dup numbers, negative lines, header-account postings); a real credit-note flow; automatic invoice numbering; the 3-way match and approval limits actually enforcing; and a clean Arabic UI I can put in front of my staff. That's a couple of weeks of hardening on a foundation that's already largely there — show me that build with a reference customer running it and I'd switch from Odoo.
