# CyMed Pricing

> **DRAFT — PENDING LEGAL REVIEW**
> **Contains INTERNAL SECTIONS — Redact before sharing externally**

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Commercial Lead — TBD>` |
| Review cadence | Quarterly (or on tier/currency change) |

---

## 1. Editions

CyMed is sold as a set of edition-based subscriptions. A tenant licenses one or more editions; each edition unlocks a scoped set of modules. The Ecosystem add-on unlocks cross-tenant referrals, shared clinical records with consent, and marketplace features.

| Edition | Scope | Included modules | Primary billing unit |
|---|---|---|---|
| **Clinic** | Single- or multi-site outpatient practice | EMR-Lite, scheduling, patient portal, e-Rx (basic), billing (cash + basic insurance), inventory-lite | Active provider / month |
| **Hospital** | Multi-department inpatient + outpatient | Full EMR, CPOE, nursing, OR, ADT, pharmacy formulary, lab/imaging orders, RCM, CDSS, incident reporting | Active provider / month |
| **Lab** | Standalone diagnostic laboratory | LIS, analyzer interfaces (HL7 / ASTM), QC, result validation, patient / referrer portals | Analyzer / month |
| **Imaging** | Radiology / imaging center | RIS + DICOM ingestion, worklist, reporting, PACS-lite, teleradiology | Modality room / month |
| **Pharmacy** | Retail / hospital-attached pharmacy | Dispense, inventory, drug interactions, insurance adjudication, controlled substance ledger | Workstation / month |
| **Ecosystem add-on** | Cross-tenant network | Referrals, shared record with patient consent, e-Rx routing to any CyMed pharmacy, network analytics | Flat per tenant / month + variable per network transaction |

---

## 2. Tiers

Each edition is offered in three tiers. Tiers differ by SLA, support hours, and enabled feature groups (AI CDSS, advanced analytics, custom integrations).

| Tier | Intended buyer | SLA | Support | Feature ceiling |
|---|---|---|---|---|
| **Pilot** | 90-day proof of value; single site | 99.5% (best effort) | Business hours, email | Core modules only; AI CDSS in shadow mode |
| **Standard** | Production, single tenant, up to ~5 sites | 99.9% | Business hours + on-call SEV1 | All modules; AI CDSS active with local sign-off |
| **Enterprise** | Multi-site / multi-tenant group; regulated buyer | 99.95% | 24/7 for SEV1–SEV2 | All modules + custom integrations + private tenancy option + dedicated CSM |

---

## 3. Billing Model

Base subscription = `Σ (edition_unit_price × unit_count × tier_multiplier)`, billed monthly or annually in advance.

| Edition | Billing unit | Definition of "active" |
|---|---|---|
| Clinic | Active provider / month | Any provider with ≥ 1 signed encounter in the month |
| Hospital | Active provider / month | Any provider (physician, nurse practitioner, resident) with ≥ 1 signed order or note |
| Lab | Analyzer / month | Any configured analyzer interface in the month, whether or not it produced results |
| Imaging | Modality room / month | Any configured modality (CT, MR, US, XR, MG room) in the month |
| Pharmacy | Workstation / month | Any concurrently-licensed dispense workstation |
| Ecosystem | Flat + variable | Base fee per tenant + per-transaction fee per referral / cross-tenant e-Rx / shared-record grant |

### 3.1 Currency table (list price, per unit / month)

Prices are list. All figures excl. VAT / withholding tax. FX indicative only.

| Edition / Tier | SAR | JOD | USD |
|---|---:|---:|---:|
| Clinic — Pilot | 220 | 60 | 59 |
| Clinic — Standard | 380 | 105 | 99 |
| Clinic — Enterprise | 640 | 175 | 169 |
| Hospital — Pilot | 340 | 95 | 89 |
| Hospital — Standard | 600 | 165 | 159 |
| Hospital — Enterprise | 1,050 | 285 | 279 |
| Lab — Pilot (per analyzer) | 750 | 205 | 199 |
| Lab — Standard | 1,300 | 355 | 349 |
| Lab — Enterprise | 2,250 | 615 | 599 |
| Imaging — Pilot (per modality room) | 2,100 | 575 | 559 |
| Imaging — Standard | 3,700 | 1,015 | 979 |
| Imaging — Enterprise | 6,400 | 1,755 | 1,699 |
| Pharmacy — Pilot (per workstation) | 450 | 125 | 119 |
| Pharmacy — Standard | 800 | 220 | 209 |
| Pharmacy — Enterprise | 1,400 | 385 | 369 |
| Ecosystem add-on — flat (per tenant) | 1,500 | 410 | 399 |
| Ecosystem add-on — per network txn | 3.5 | 1.0 | 0.95 |

### 3.2 One-time fees

Charged at contract signature, invoiced by milestone (30 / 40 / 30). List in USD; local currency at contract FX.

| Line item | Clinic | Hospital | Lab | Imaging | Pharmacy |
|---|---:|---:|---:|---:|---:|
| Implementation (config, environment, go-live) | 6,000 | 45,000 | 18,000 | 22,000 | 8,000 |
| Data migration (per legacy system) | 3,500 | 25,000 | 9,000 | 14,000 | 4,500 |
| Training (role-based, per cohort of 10) | 1,200 | 4,500 | 2,200 | 2,600 | 1,500 |
| Custom integration (per endpoint) | 2,500 | 6,500 | 4,000 | 5,500 | 3,000 |

### 3.3 Volume discounts

Applied to the monthly subscription base, tiered by aggregate units across all editions.

| Aggregate active units / month | Discount |
|---:|---:|
| 1 – 25 | 0% |
| 26 – 100 | 8% |
| 101 – 300 | 15% |
| 301 – 750 | 22% |
| 751+ | Negotiated (floor 28%) |

### 3.4 Multi-year discounts

Applied on top of volume discount, requires prepayment or committed spend.

| Term | Discount |
|---:|---:|
| 1 year | 0% |
| 2 years | 6% |
| 3 years | 12% |
| 5 years | 18% (Enterprise only) |

---

## 4. Fair-use, overages, and adjustments

- **Active-unit true-up**: monthly; overages billed at list, credits carried forward up to 2 months.
- **Storage**: 20 GB per active provider / analyzer / modality room / workstation included; overage USD 0.09 / GB / month.
- **API calls**: 100k / month per edition included; overage USD 0.60 / 10k calls.
- **DICOM object storage**: 500 GB / modality room included; overage USD 0.05 / GB / month.

---

## 5. INTERNAL — NOT FOR CUSTOMER

> The material below is for commercial planning. It must not appear in customer-facing collateral or proposals.

### 5.1 Gross-margin planning table

Assumes managed cloud in-region (KSA / UAE / EU / US), 100% SaaS delivery.

| Edition / Tier | List (USD / unit / mo) | Direct COGS (USD) | GM % target | Floor discount (max) |
|---|---:|---:|---:|---:|
| Clinic — Standard | 99 | 22 | 78% | 35% |
| Clinic — Enterprise | 169 | 34 | 80% | 30% |
| Hospital — Standard | 159 | 40 | 75% | 30% |
| Hospital — Enterprise | 279 | 62 | 78% | 25% |
| Lab — Standard | 349 | 78 | 78% | 30% |
| Lab — Enterprise | 599 | 118 | 80% | 25% |
| Imaging — Standard | 979 | 235 | 76% | 25% |
| Imaging — Enterprise | 1,699 | 375 | 78% | 22% |
| Pharmacy — Standard | 209 | 46 | 78% | 30% |
| Pharmacy — Enterprise | 369 | 78 | 79% | 25% |
| Ecosystem — flat | 399 | 55 | 86% | 20% |
| Ecosystem — per txn | 0.95 | 0.11 | 88% | 15% |

### 5.2 Deal-desk rules

1. Any discount beyond volume + multi-year requires deal-desk approval.
2. Discounts below the per-line floor require CFO sign-off.
3. Free Pilot conversions must credit at most 50% of prior Pilot fees against Standard year-one.
4. Local FX must be refreshed monthly; freeze the FX only at contract signature.
5. Ecosystem per-txn fee is not discountable below USD 0.35 without CEO sign-off.
