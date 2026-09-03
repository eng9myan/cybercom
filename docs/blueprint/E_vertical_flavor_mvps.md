# Section E — Vertical Flavor MVP Blueprints

> Four MVPs, prioritised by **speed-to-learning × existing code leverage × ROI**.
> Each is scoped to **go live in 6–8 weeks** on top of the canonical core (Section C/D).
> Order: **Retail (1) → Health (2) → AutoParts (3) → Grocery (4)**.

## Prioritisation rationale

| Flavor | Existing code | Time-to-learning | Regulatory load | ROI signal | Wave |
|---|---|---|---|---|---|
| Retail / F&B | High (CyCom catalog, POS+KDS, sales) | Fast (short sales cycle, JO beachhead) | Medium (ZATCA, VAT) | Fast MRR, referenceable in weeks | **1** |
| Health | High (CyMed 16 apps) but unverified | Slow (long B2B cycle, clinical validation) | High (NPHIES, PDPL-health, licensing) | High ACV, sticky, cross-domain showcase | **2** |
| AutoParts | Low (needs fitment/xref data model) | Medium | Medium (ZATCA B2B) | Solid mid-market ACV | **3** |
| Grocery/Hypermarket | Medium (inventory, POS) | Medium | Medium-High (volume, weighing, promos) | High volume, lower margin | **4** |

---

## E.1 RetailFlavour MVP (F&B + general retail)

### Core MVP scope (6–8 weeks)
- Onboarding: describe-your-business → AI-propose → RetailFlavour provisioned (catalog + POS + inventory + basic GL + VAT preset) with a seeded demo.
- **Catalog**: products/variants/categories, barcodes, price lists, VAT class, images (CyVault).
- **POS**: hardware-agnostic web + Android; sessions, cash management, split/multi-tender (cash/card/wallet), receipts (print + digital), returns/exchange, discounts + approval workflow, layaway.
- **Live KDS** for F&B: order → kitchen screen, bump, prep-time, station routing.
- **Inventory**: multi-branch stock, transfers, low-stock alerts, AVCO costing, stock-take via SyncInventory.
- **Finance**: auto journal posting (revenue/tax/COGS), daily Z-report, VAT summary, **ZATCA Phase 2 clearance** for KSA tenants (XML + QR + Fatoora), simplified tax invoice for B2C.
- **Multi-branch consolidation**: one dashboard, per-branch and rolled-up sales/margin.
- Arabic/RTL for POS + receipts (first slice of the i18n workstream).

### Flavor add-ons (post-MVP, feature-flagged)
- Delivery aggregator sync: Talabat / Jahez / HungerStation / Deliveroo (menu push, order pull, status).
- CyDrive own-delivery dispatch.
- Loyalty + promotions engine (points, tiers, basket rules, coupons).
- Recipe/BOM + theoretical vs actual food cost; waste tracking.
- Table management / floor plan (hospitality sub-profile); reservations.
- Online storefront (headless commerce on the same catalog).
- Payroll (local) + staff scheduling + tip pooling.

### Cross-domain workflows (ecosystem proof)
- Retail pharmacy **inside a clinic tenant**: HealthFlavour + RetailFlavour on one tenant; OTC sale at POS posts to the same GL as patient billing; shared inventory for dispensed vs retail stock.
- Hotel: HospitalityFlavour rooms + RetailFlavour gift shop + F&B outlets → one night-audit, one consolidated P&L.
- Franchise: HQ tenant sees franchisee tenants' sales via ConsentGrant-based cross-tenant reporting.

### UX patterns / layout templates
- `pos_register` (touch-first, large targets, offline indicator), `kds_board`, `counter_return`,
  `daily_close`, `branch_overview` (map + tiles), `catalog_grid`, `product_editor`.
- Design-system: dark-friendly POS, high-contrast, RTL-mirrored, keyboard + barcode-scanner first.

### Pilot KPIs
| KPI | Target |
|---|---|
| Onboarding: signup → first sale | < 1 day (self-serve) |
| POS ring latency p95 | < 400 ms |
| Offline resilience | 100% of sales captured during a 30-min outage, auto-synced |
| Stock accuracy (cycle count) | > 97% |
| ZATCA clearance success | > 99.5%, p95 < 10 s |
| Pilot count wave 1 | 3 JO F&B/retail SMBs live + 1 reference |

### Go / no-go gates
- **Go to pilot**: signup→pay→provision→sale loop green in staging against real Keycloak + one live PSP; ZATCA sandbox clearance passing; RTL POS usable by an Arabic-first cashier in a hallway test.
- **Go to GA**: 3 pilots stable 30 days, < 1 P1/week, NPS ≥ 40, support first-response < 4h.

---

## E.2 HealthFlavour MVP (clinic / polyclinic first, hospital later)

### Core MVP scope (6–8 weeks — assumes CyMed apps stabilised)
- Onboarding: clinic profile → HealthFlavour (scheduling + encounters + billing + pharmacy + basic RCM) on canonical core.
- **Scheduling**: provider calendars, online booking, reminders (SMS/WhatsApp), check-in, no-show handling, deposits via Order.
- **Encounter**: problem list, ICD-11 diagnoses, procedures, clinical notes, vitals; e-prescription; lab/imaging orders (ClinicalOrder).
- **Patient billing**: encounter → Invoice (cash or insurance split); ZATCA-compliant invoice; patient statement.
- **Pharmacy**: dispensing as Order (`profile=pharmacy`), stock + expiry, controlled-substance register.
- **RCM / insurance**: build a Claim from billable items; **NPHIES submission** (KSA) / eClaim (UAE) with status tracking; remittance posting.
- **Patient portal**: appointments, results, invoices, pay online.
- PDPL-health data handling: PHI field encryption, consent capture, access audit, in-region storage.

### Flavor add-ons
- Full hospital: wards, admissions, OT scheduling, nursing, bed management.
- FHIR R4 API for HIE/national exchange; DICOM imaging (CyVault archive) + basic viewer.
- AI clinical decision support (flagged, human-in-loop per `docs/ai/HUMAN_REVIEW_REQUIREMENTS.md`).
- Lab LIS depth (analyzer interfaces), radiology RIS.
- Insurance pre-authorisation workflow; package/bundle pricing.
- Telehealth (video) + remote e-Rx.

### Cross-domain workflows
- **Hospital procurement via shared catalog**: medical supplies + pharmacy + cafeteria + branded merch all as canonical PurchaseOrders → one AP ledger.
- **Patient-facing retail**: hospital gift shop / optical / pharmacy retail as RetailFlavour on the same tenant; patient can pay a consolidated bill.
- **Corporate health**: an employer tenant books staff clinic visits; billing flows employer↔clinic via ConsentGrant + cross-tenant Invoice.
- Cross-tenant referral: clinic A refers to specialist clinic B with a scoped clinical-summary ConsentGrant.

### UX patterns
- `provider_schedule`, `encounter_workspace` (SOAP layout, order sets), `patient_summary`,
  `front_desk_checkin`, `claim_worklist`, `pharmacy_dispense`, `patient_portal_home`.
- Calm clinical palette, large legible type, minimal clicks per encounter, Arabic patient-facing.

### Pilot KPIs
| KPI | Target |
|---|---|
| Assisted onboarding | < 2 weeks clinic-live |
| Encounter documentation time | ≤ baseline (no worse than paper/incumbent) |
| Claim first-pass acceptance | > 90% |
| Clearance/claim submission latency | p95 < 30 s |
| PHI access audit coverage | 100% of reads logged |
| Pilot count wave 1 | 2 clinics (1 JO, 1 KSA or UAE) + 1 multi-domain (clinic + pharmacy retail) |

### Go / no-go gates
- **Go to pilot**: clinical data-model review signed by a licensed clinician; NPHIES/eClaim sandbox accepted; PDPL-health DPIA complete; pentest of PHI paths passed.
- **Go to GA**: 2 pilots 60 days stable; zero PHI incidents; claim acceptance > 90%; regulator/licensing box checked per country.

---

## E.3 AutoPartsFlavour MVP

### Core MVP scope (6–8 weeks)
- Onboarding: parts business → AutoPartsFlavour (catalog w/ fitment + inventory + counter POS + B2B orders + procurement + GL/VAT).
- **Parts catalog**: OE number + aftermarket cross-reference + **supersession chains**; vehicle fitment (make/model/year/engine); brand, category, unit.
- **Counter sale**: lookup by plate/VIN/vehicle or part number; real-time multi-branch availability; quote → order → invoice; core-charge handling; customer credit accounts.
- **Inventory**: multi-warehouse, bin locations, min/max + reorder, inter-branch transfer, supplier lead times.
- **Procurement**: supplier catalogs, PO from reorder suggestions, goods receipt, landed cost.
- **B2B**: trade pricing tiers, credit limits, statements, ZATCA B2B e-invoice (full, with buyer VAT).
- Warranty / returns register.

### Flavor add-ons
- Supplier catalog auto-ingestion (ACES/PIES-style feeds where available + regional supplier price files).
- Garage/workshop sub-module: job cards, labour, service bays (uses Scheduling), estimate→invoice.
- Marketplace listing via CyMart; dropship.
- Tyre-specific attributes (size, load/speed index, DOT).

### Cross-domain workflows
- Auto group: parts (AutoPartsFlavour) + workshop (Scheduling) + car wash / accessories retail (RetailFlavour) + fleet (CyDrive) on one tenant, one P&L.
- Fleet customer tenant orders parts B2B; their maintenance schedule triggers PO suggestions.

### UX patterns
- `parts_lookup` (vehicle selector + results grid + availability), `counter_ticket`,
  `interchange_view` (OE ↔ aftermarket ↔ superseded), `branch_availability_map`, `b2b_account`.

### Pilot KPIs
| KPI | Target |
|---|---|
| Onboarding (assisted, catalog load) | < 2 weeks |
| Part lookup → quote | < 30 s at counter |
| Stock fill rate | > 92% |
| Dead-stock ratio (12-mo no-sale) | trending down |
| Cross-reference coverage | > 80% of active SKUs |
| Pilot count | 2 distributors (1 JO, 1 KSA) |

### Go / no-go gates
- **Go to pilot**: fitment + xref + supersession model handles a real 5k-SKU supplier file; multi-branch availability accurate in a 2-branch test.
- **Go to GA**: 2 pilots 45 days; counter staff prefer it to incumbent in a blind task test; ZATCA B2B invoices accepted.

---

## E.4 GroceryHypermarketFlavour MVP

### Core MVP scope (6–8 weeks)
- Onboarding: grocery/minimart → GroceryFlavour (high-SKU catalog + POS + inventory w/ expiry + promotions + GL/VAT).
- **High-volume POS**: fast scan, weighed items (scale integration + PLU), offline-first, queue-busting, multi-tender, loyalty lookup.
- **Catalog**: 10k+ SKUs, barcode + PLU, pack/each UoM, supplier + margin, VAT class (many zero-rated foods).
- **Inventory**: batch + expiry, FEFO picking, shrinkage/wastage, shelf-edge label export, multi-store replenishment from a DC.
- **Promotions**: multibuy, threshold, time-boxed, member price; markdown for near-expiry.
- **Supplier**: rebate/margin agreements, invoice matching (PO ↔ GRN ↔ invoice 3-way).
- Finance: daily reconciliation across many terminals, cash pickups, bank deposit.

### Flavor add-ons
- Hypermarket scale: departments, concessions, sub-tenant leased areas, scan-and-go app.
- E-grocery: online catalog + slot booking + picking app + CyDrive/aggregator delivery.
- Weighbridge (for wholesale), butchery/bakery production, deposit-return schemes.
- Central buying across stores; planogram.

### Cross-domain workflows
- Fuel station + convenience store: FuelStationFlavour (pumps/dip/wet-stock) + GroceryFlavour C-store + F&B on one site tenant.
- Grocery chain HQ: cross-tenant/branch consolidated buying, margin, and rebate reporting.

### UX patterns
- `grocery_register` (scan-speed optimised, weighed-item prompt), `price_check`,
  `expiry_worklist`, `replenishment_board`, `promo_builder`, `supplier_match_3way`.

### Pilot KPIs
| KPI | Target |
|---|---|
| Scan throughput | ≥ 20 items/min sustained |
| Offline: sales captured during outage | 100% |
| Expiry write-off as % of sales | trending down; visibility 100% |
| 3-way match auto-clear rate | > 85% |
| Promo setup time | < 5 min per promo |
| Pilot count | 2 (1 minimart, 1 mid-size supermarket) |

### Go / no-go gates
- **Go to pilot**: POS sustains 20 items/min with a scale in a lane test; 10k-SKU catalog imports clean; promotions engine handles 5 concurrent overlapping offers correctly.
- **Go to GA**: 2 pilots 45 days; cashier task-time ≤ incumbent; daily reconciliation balances unattended.

---

## E.5 Shared "definition of a flavor MVP done"

1. Provisionable from the flavor engine in one onboarding call (Section D API 1).
2. Its layout templates render from the design system — zero bespoke frontend code.
3. All data on the canonical model (extensions via `attributes` profile, no forked tables).
4. ZATCA/VAT correct for KSA + JO + UAE where the flavor transacts.
5. Emits domain events; appears in cross-domain analytics.
6. Has a seeded demo tenant for sales.
7. KPI dashboard pack ships with it.
8. Arabic/RTL on all customer-facing and high-use operator screens.
9. Threat-modelled; PII/PHI paths pentested where relevant.
10. Runbook + support playbook written.
