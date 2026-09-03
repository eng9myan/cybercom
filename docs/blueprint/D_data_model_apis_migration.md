# Section D — Canonical Data Model, Core APIs, Migration

## D.1 Canonical entity brief (ERD)

All entities carry: `id` (UUID), `tenant_id` (FK, RLS-enforced), `created_at`, `updated_at`,
`created_by`, `version` (optimistic lock), `attributes` (JSONB, schema-registered per flavor
profile). Soft-delete via `deleted_at`.

### Platform / tenancy

| Entity | Brief |
|---|---|
| **Tenant** | The customer account. Holds `residency_region`, `subscription_id`, `flavor_set[]`, `encryption_key_ref`, compliance flags, status (trial/active/suspended). Root of all isolation. |
| **Organization** | A legal/operating entity within a Tenant (multi-company). Owns its own GL, tax registration (VAT/CR number), and can be consolidated. A Tenant has ≥ 1 Organization. |
| **Branch / Location** | A physical or logical site under an Organization (store, clinic, warehouse, bay, pump island). Pricing, stock, POS terminals, and staff attach here. |
| **User** | An identity (from CyIdentity/Keycloak). Global principal; gains access to Tenants via Membership. |
| **Membership** | User ↔ Tenant (+ optional Organization/Branch scope) with `role_id`. The access-granting join. |
| **Role** | Named permission bundle, tenant-scoped or system. Maps to a set of Permissions. |
| **Policy** | Attribute/condition-based rule for cross-tenant access, consent grants, and step-up-auth requirements. Evaluated default-deny. |
| **Subscription** | Tier (Starter/Pro/Enterprise), entitlements, limits (locations/terminals/providers/users), billing cycle, PSP customer ref. |
| **VerticalFlavor** | Versioned flavor definition (module set, layout templates, tax presets, workflows, KPI pack, seed data, required integrations, regulatory packs). Referenced by Tenant.flavor_set. |
| **LayoutTemplate** | Named screen composition (slots → design-system components) belonging to a flavor. |
| **Integration** | A configured connector instance for a Tenant (PSP, delivery aggregator, Fatoora, NPHIES, WPS bank). Holds credential-vault ref, status, sync cursors. |
| **APIKey / OAuthClient** | Developer-portal credentials for a Tenant; scopes, rate-limit tier, rotation metadata. |
| **AuditEvent** | Immutable record: actor, action, resource, tenant, before/after hash, trace id, timestamp. Hash-chained. |
| **ConsentGrant** | Tenant-A → Tenant-B (or User → Tenant) permission for a defined data scope + purpose + expiry. Powers cross-domain workflows lawfully. |
| **DomainEvent** | Outbox row: type, aggregate id, tenant, payload (schema-versioned), published_at, offset. |

### Commerce / operations

| Entity | Brief |
|---|---|
| **Catalog** | A named product collection scoped to Organization (or shared). Has a `catalog_profile` (retail / auto_parts / jewelry / grocery / pharmacy / service) that enables typed attributes. |
| **Product** | A sellable/stockable concept: name, category, tax class, base UoM, `catalog_profile` attributes (e.g. fitment, karat, PLU, ATC code). Parent of Variants. |
| **Variant** | A concrete purchasable form of a Product (size/colour/pack). Carries its own barcode(s). |
| **SKU** | Stock-keeping unit = Variant × (optionally) Branch. The unit inventory and costing track. |
| **PriceList** | Currency + customer-segment + date-ranged prices; supports rate-based (live gold), weight-based, tiered, and promotional pricing rules. |
| **Promotion** | Rule-based discount/loyalty offer (basket, item, BOGO, threshold). Consumed by Orders. |
| **InventoryLocation** | A stockholding place (warehouse, store back-room, bay, fridge). Under a Branch. |
| **StockItem** | SKU × InventoryLocation: on-hand, reserved, valuation (FIFO/AVCO), lot/serial/expiry sublevels. |
| **StockMove** | An immutable inventory transaction (receipt, sale, transfer, adjustment, return) linking source/dest, qty, cost, reason, reference doc. |
| **Order** | The universal transaction aggregate: header (customer, branch, channel: POS/online/marketplace/B2B, status via state machine), lines (SKU, qty, price, tax, discount), payments, fulfilments. POS sales, e-com orders, B2B quotes→orders, and service orders are all Orders with a `type`. |
| **Fulfilment** | A shipment/handover/pickup/delivery against Order lines; links to CyDrive/aggregator dispatch. |
| **Payment** | A money movement against an Order or Invoice: method, PSP ref, amount, currency, status, captured/refunded, tokenised instrument ref. |
| **Customer** | A buyer/patient/account: contact, segment, loyalty balance, credit terms, tax id. In Health, extended by patient attributes + MRN. |
| **Vendor** | A supplier: contact, catalogs, payment terms, rebate agreements, tax id. |
| **PurchaseOrder** | Request→approve→PO→GoodsReceipt chain against a Vendor; lines mirror Order lines. |
| **Invoice** | AR or AP document: lines, tax breakdown, currency + rate, status, **e-invoice fields** (UUID, hash, previous-hash, QR, ZATCA clearance status + cleared XML ref). |
| **LedgerAccount** | Chart-of-accounts node per Organization. |
| **JournalEntry** | Balanced set of debit/credit lines posted from a business event (sale, receipt, payroll, payment); immutable once posted. |
| **TaxRule** | Country/region + product-class + transaction-type → rate, treatment (standard/zero/exempt/reverse-charge), reporting box. Presets per flavor. |
| **Localization** | Per-tenant/per-org locale, currency, number/date format, calendar, RTL flag, translated overrides. |

### People

| Entity | Brief |
|---|---|
| **Employee** | Person employed by an Organization: contract, grade, pay elements, bank/IBAN, national id/Iqama (encrypted), GOSI/insurance number. |
| **PayrollBatch** | A payroll run for an Organization + period: status, totals, country calculation profile (GOSI/gratuity/GPSSA/WPS). |
| **Payslip** | Per-Employee result within a PayrollBatch: earnings, deductions, employer contributions, net, WPS line. |
| **Appointment** | A booked slot: resource (provider/bay/table), customer, service, start/end, status (booked/checked-in/completed/no-show), links to an Order for billing. |

### Health extensions (HealthFlavour — on the same core)

| Entity | Brief |
|---|---|
| **Patient** | = Customer + MRN, demographics, insurance coverage, consent records. PHI columns encrypted per-tenant. |
| **Encounter** | A clinical visit (= Appointment realised): diagnoses (ICD-11), procedures, orders (lab/imaging/Rx), notes. |
| **ClinicalOrder** | Lab/imaging/pharmacy order raised in an Encounter; fulfilled by `laboratory`/`imaging`/`pharmacy`; billed via Order/Invoice. |
| **Claim** | Insurer claim built from an Encounter's billable items; NPHIES submission status. |

Health entities are typed extensions/relations of core entities — **not a parallel model**. `pharmacy` dispensing is an Order with `catalog_profile=pharmacy`; hospital procurement is a PurchaseOrder; patient billing is an Invoice.

### ERD relationships (compact)

```
Tenant 1─* Organization 1─* Branch 1─* InventoryLocation
Tenant 1─* Membership *─1 User ;  Membership *─1 Role *─* Permission
Tenant 1─* VerticalFlavor ;  VerticalFlavor 1─* LayoutTemplate
Organization 1─1 Catalog(default) 1─* Product 1─* Variant 1─* SKU
SKU 1─* StockItem *─1 InventoryLocation ;  StockItem 1─* StockMove
Order *─1 Customer ;  Order 1─* OrderLine *─1 SKU ;  Order 1─* Payment ;  Order 1─* Fulfilment
Order 1─0..1 Invoice 1─* JournalEntry ;  Invoice *─1 TaxRule(applied)
PurchaseOrder *─1 Vendor ;  PurchaseOrder 1─* GoodsReceipt 1─* StockMove
Organization 1─* Employee 1─* Payslip *─1 PayrollBatch
Appointment *─1 Customer ;  Appointment 0..1─1 Order ;  Encounter 1─1 Appointment
Encounter 1─* ClinicalOrder ;  Encounter 1─0..1 Claim
Tenant 1─* Integration ;  Tenant 1─* ConsentGrant ;  every write ─* DomainEvent ─* AuditEvent
```

## D.2 Core API contracts (OpenAPI-style outline)

Base: `https://api.cybercom.<region>/api/v1`. Auth: `Authorization: Bearer <OIDC access token>`,
`X-Tenant-ID` (or resolved from token). All responses envelope: `{ data, meta, errors }`.
Idempotency: `Idempotency-Key` header on all POST that create money/stock movement.

### 1. `POST /onboarding/tenants` — CreateTenantOnboarding

```
request:
  organization: { legal_name, country, vat_number?, cr_number? }
  admin_user:   { email, name, phone }
  flavors:      ["RetailFlavour"]           # 1..n, composed
  residency_region: "me-central-1"
  subscription_tier: "professional"
  locale:       { language: "ar", currency: "SAR" }
  seed_demo:    false
response 202:  { data: { tenant_id, provisioning_job_id, status: "provisioning" } }
events:        tenant.created, provisioning.started → provisioning.completed
notes:         async; poll GET /onboarding/jobs/{id}; creates Keycloak realm/user,
               composes flavor(s), seeds COA + tax presets + layout templates,
               issues first subscription invoice.
```

### 2. `POST /catalog/{catalog_id}/products` — CreateShopCatalog (bulk)

```
request:
  items: [ { name, category, tax_class, base_uom, catalog_profile_attributes: {...},
             variants: [ { sku_code, barcode, attributes, price: {list, currency},
                           opening_stock: [ { location_id, qty, unit_cost } ] } ] } ]
response 207:  per-item { index, status, product_id?, errors? }   # multi-status
validation:    profile schema enforced (e.g. auto_parts requires fitment[]; jewelry
               requires karat + making_charge_rule; grocery weighed requires plu)
events:        catalog.product.created (per item), inventory.stock.opened
```

### 3. `POST /orders` + `POST /orders/{id}/checkout` — CreateOrder / Checkout

```
POST /orders
request:  { branch_id, channel: "pos"|"online"|"b2b"|"marketplace"|"service",
            customer_id?, lines: [ { sku_id, qty, unit_price_override?, discount? } ],
            appointment_id? }
response 201: { data: { order_id, status: "draft", totals: {...} } }

POST /orders/{id}/checkout
request:  { payments: [ { method: "card"|"cash"|"wallet"|"insurance"|"credit",
                          amount, psp_token?, provider? } ],
            fulfilment: { mode: "pickup"|"delivery"|"dine_in"|"ship", address?, dispatch: "cydrive"|"talabat"? },
            invoice: { issue: true, buyer_tax_id? } }
response 200: { data: { order_id, status: "confirmed", invoice_id,
                        einvoice: { zatca_status: "cleared"|"reported"|"pending", qr, uuid },
                        payments: [...], kds_ticket_id? } }
side effects: StockMove (sale), JournalEntry (revenue+tax+COGS), Payment capture via PSP,
             Invoice + ZATCA clearance call, KDS ticket if F&B, Fulfilment + dispatch.
events:      order.confirmed, inventory.stock.moved, finance.invoice.issued,
             finance.invoice.cleared, payment.captured, fulfilment.requested
```

### 4. `POST /inventory/sync` — SyncInventory

```
request:  { source: "supplier_feed"|"stocktake"|"external_wms", location_id,
            mode: "absolute"|"delta",
            lines: [ { sku_code, qty, unit_cost?, lot?, expiry?, serial? } ],
            reconcile: true }
response 202: { data: { job_id } }   # async for large feeds
result:   creates StockMove adjustments to reconcile; flags variances > threshold for review;
          updates AVCO/FIFO cost layers.
events:   inventory.sync.completed, inventory.variance.flagged
```

### 5. `POST /scheduling/appointments` — CreateAppointment

```
request:  { branch_id, resource_id, service_id, customer_id, start, end,
            create_encounter?: true,          # HealthFlavour
            notify: ["sms","email"] }
response 201: { data: { appointment_id, status: "booked", encounter_id?,
                        conflicts: [] } }
rules:    resource availability check, double-book policy, deposit via Order if configured.
events:   scheduling.appointment.booked, (health) clinical.encounter.opened
```

### 6. `POST /payroll/batches` + `POST /payroll/batches/{id}/run` — GeneratePayroll

```
POST /payroll/batches
request:  { organization_id, period: { year, month }, country_profile: "SA_GOSI"|"AE_GRATUITY"|"JO",
            employee_scope: "all"|[ids] }
response 201: { data: { batch_id, status: "draft", employee_count } }

POST /payroll/batches/{id}/run
response 200: { data: { batch_id, status: "calculated",
                        totals: { gross, deductions, employer_contrib, net },
                        payslips: n, wps_file_ref? } }
POST /payroll/batches/{id}/post   → JournalEntry, locks the batch, generates WPS SIF file.
events:   hr.payroll.calculated, hr.payroll.posted, finance.journal.posted
```

## D.3 Migration: CyShop + CyCom + CyMed → one canonical schema

### Principle

CyCom's core + `platform/` **is** the canonical target. CyShop migrates in fully (it is
duplicate). CyMed **keeps its clinical apps** but re-homes its shared concerns (identity,
tenant, catalog, orders/pharmacy, inventory, finance, HR) onto the canonical core.

### Source → target mapping (high level)

| Source | Source entities | Target | Rule |
|---|---|---|---|
| CyShop `tenants` | Tenant, Store | `platform/tenant` Tenant + Organization + Branch | 1 CyShop tenant → 1 Tenant + 1 Organization; stores → Branches |
| CyShop `identity` (own JWT) | User, Token | CyIdentity / Keycloak | create Keycloak users; issue password-reset; map roles → canonical Roles; **deprecate CyShop JWT** |
| CyShop `catalog` | Product, Variant, Category | canonical Catalog/Product/Variant/SKU | direct (schema already ported to CyCom); attach `catalog_profile=retail` |
| CyShop `inventory` | StockItem, Move | canonical StockItem/StockMove | map locations to Branch/InventoryLocation; recompute cost layers |
| CyShop `sales` / `pos` | Order, PosOrder, Receipt | canonical Order (`type=pos`/`online`) + Fulfilment + Payment | state-machine mapping table; preserve original ids in `attributes.legacy_id` |
| CyShop `accounting` | Account, Entry | canonical LedgerAccount/JournalEntry | map COA; migrate posted entries as opening balances if COA differs |
| CyShop `hr`/`payroll` | Employee, Payslip | canonical Employee/Payslip | direct; re-run current period on canonical engine to validate |
| CyShop `purchasing` | PO, Receipt | canonical PurchaseOrder/GoodsReceipt | direct |
| CyShop `notifications`/`audit` | — | `platform/notifications` + `platform/audit` | forward-only; archive old audit read-only |
| CyCom | all `cycom/products/cycom/*` | canonical (is target) | in place; add `tenant.residency_region`, `flavor_set`; RLS rollout |
| CyMed `core`/`commercial`/`ecosystem` | tenant/org/billing | canonical `platform/tenant` | re-point CyMed to shared tenant; consent grants for cross-domain |
| CyMed `pharmacy` | Drug, Dispense | canonical Catalog(`profile=pharmacy`) + Order | dispensing = Order; keep clinical link |
| CyMed `hospital`/`clinic` procurement, stock | — | canonical Procurement/Inventory | re-home; clinical-specific fields → `attributes` |
| CyMed `rcm`/`payments` | Invoice, Claim, Payment | canonical Invoice/Payment + Claim extension | Invoice canonical; Claim stays a health extension |
| CyMed `fhir_r4`/`imaging`/`laboratory`/`ai_cds`/`patient_portal`/`provider_portal` | clinical | **stay in CyMed apps** as HealthFlavour modules | only relations to core (Encounter→Order, ClinicalOrder→fulfilment) change |

### Phased plan

| Phase | Scope | Method | Rollback |
|---|---|---|---|
| **M0 — Freeze & reconcile** | resolve the 3 checkouts (Section 00); pick canonical branch; push to `develop`; tag `pre-migration` | git | revert to tag |
| **M1 — Schema convergence** | add canonical fields (residency, flavor_set, einvoice, encryption refs); expand/contract migrations; RLS behind flag | additive migrations, no data move | drop added columns; flag off |
| **M2 — CyShop dry-run** | migrate a **copy** of CyShop prod data into a staging canonical tenant; run reconciliation suite (row counts, GL trial-balance equality, stock valuation equality, order-total checksums) | ETL scripts + `attributes.legacy_id` | discard staging tenant |
| **M3 — CyShop cutover** | freeze CyShop writes (maintenance window); final delta ETL; flip DNS/clients to canonical; keep CyShop DB read-only 90 days | scripted, < 2h window per tenant | re-open CyShop writes, revert DNS (data-loss window = the frozen delta only) |
| **M4 — CyMed re-home (shared concerns)** | re-point CyMed tenant/identity/billing to `platform/`; migrate pharmacy/procurement/inventory/finance; clinical apps unchanged | per-tenant, staged, consent-grant setup | CyMed keeps its own tables until M4 verified; feature-flag the re-point |
| **M5 — Decommission** | archive CyShop repo + DB snapshot; remove CyShop deploy pipelines; update docs; delete `Cybercom-launch` | — | snapshots retained 1 year |

### Data-quality gates (must pass before each cutover)

- Row-count parity per entity (± 0, or explained).
- **GL trial balance**: source and target net to the same per Organization per period.
- **Inventory valuation**: total on-hand value equal within rounding tolerance per location.
- **Order totals checksum**: Σ(order grand totals) equal; no orphan lines/payments.
- **Auth**: every active source user has a working canonical login (verified by forced-reset completion rate).
- **No PII in logs** during ETL; ETL runs in-region only.
- Reconciliation report signed off by finance + the migration owner.

### Cutover mechanics

- Blue/green at the client layer: canonical stack live in parallel; per-tenant flag routes reads/writes.
- Idempotent, resumable ETL (checkpointed by `legacy_id`).
- Dual-write **not** used (complexity/consistency risk); instead short freeze + delta.
- Communication: 2-week notice, maintenance window in the tenant's timezone, rollback criteria published.
