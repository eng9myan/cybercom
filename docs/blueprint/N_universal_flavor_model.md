# Section N — The Universal Flavor Model

> The objective: CyberCom is the go-to system for **any** business on earth — a corner
> shop, a hospital group, a car-parts distributor, a five-star hotel, a cement factory,
> a power utility, a university, a municipality. This section is the honest engineering
> answer to "can one platform really do that?" — what makes it true, where the line is,
> and how it stays coherent instead of collapsing into a thousand forks.

## N.1 The thesis — express, don't pre-build

CyberCom does **not** become universal by shipping a hand-built product for every industry.
That is the road to 40 codebases. It becomes universal through **four mechanisms**, in order
of how often they're used:

| # | Mechanism | Who uses it | Deploy? |
|---|---|---|---|
| 1 | **Configuration** — turn core modules on/off, set tax/locale/workflow presets | every tenant, at onboarding (AI-propose) | no |
| 2 | **Flavor packs** — a versioned bundle of config + attribute profiles + layout templates + KPI packs + regulatory packs (`flavor.schema.yaml`) | product team + certified partners | no (feature-flagged) |
| 3 | **Flavor Studio** — a visual/declarative builder: custom objects, fields, relationships, workflows, screens, reports, permissions, API endpoints — all tenant-scoped, no core code | advanced tenants + partners/implementers | no (runtime metadata) |
| 4 | **Extension apps** — real code (a Django app / a service) for genuinely novel logic, installed per tenant via the developer platform | partners + CyberCom for net-new domains | yes, sandboxed |

**Rule of thumb:** if two or more target industries need the same new capability, it graduates
from Studio (3) into the core or a flavor pack (2), reviewed by CDAC. A capability that only
one niche needs stays in Studio or an extension app. The core grows deliberately and slowly;
the edges grow freely.

## N.2 The canonical primitives — why the core generalises

Every ERP vertical, no matter how exotic, decomposes into a small set of primitives. The
canonical data model (Section D) is built on these, and flavors specialise them via typed
`attributes` profiles rather than new tables:

| Primitive | Core entity | "Corner shop" | "Cement factory" | "Municipality" | "University" |
|---|---|---|---|---|---|
| **Party** | Customer / Vendor / Employee / Partner | walk-in customer | bulk buyer, aggregate supplier | citizen, contractor | student, faculty, sponsor |
| **Item** | Product / Variant / SKU (+ `catalog_profile`) | a can of cola | clinker, 42.5N bagged cement, a spare kiln bearing | a permit type, a service fee | a course, a credit-hour, a hostel bed |
| **Agreement** | Order / PurchaseOrder / Subscription / Contract | a sale | a supply contract with a delivery schedule | a permit application, a licence | an enrolment, a tuition plan |
| **Transaction/Event** | StockMove / Payment / JournalEntry / DomainEvent | ring a sale | a production declaration, a weighbridge ticket | a fee payment, an inspection result | a grade submission, a fee payment |
| **Location** | Branch / InventoryLocation / StoreLocation | the shop | quarry, crusher, kiln line, packing plant, depot | ward, office, facility | campus, building, room |
| **Resource** | Employee / Asset / Device / Vehicle | the till, the owner | kiln #2, haul truck, a maintenance crew | an inspector, a garbage truck | a lab, a lecturer, a projector |
| **Schedule** | Appointment / Shift / WorkOrder / ProductionOrder | opening hours | a production plan, a shift roster, a maintenance window | an inspection calendar, a service SLA | a timetable, an exam schedule |
| **Document** | Invoice / Receipt / GovernmentDocument / HealthRecord / Certificate | a receipt | a delivery note, a quality certificate, a lab COA | a permit PDF, a citation | a transcript, a certificate |
| **Ledger** | LedgerAccount / JournalEntry | daily cash | full cost accounting, WIP, variance | fund accounting, budget lines | fund + grant accounting |
| **Rule** | TaxRule / Policy / PricingRule / ComplianceRule | 15% VAT | environmental compliance limits, tolling | statutory fee schedules | financial-aid rules |

If a domain's needs fit these primitives + a new attribute profile + some workflows → it's a
**flavor** (mechanism 2). If it needs a genuinely new *noun* with its own lifecycle (a
`ProductionOrder` with operations and routings; a `MeterReading` with a billing determinant;
a `PermitApplication` with a statutory state machine) → that noun is added **once** to the
core as a first-class entity that every flavor can use, or lives as a Studio custom object /
extension app until it earns core status.

## N.3 Flavor Studio (the platform play)

The thing that makes "any business" credible. Modelled on Odoo Studio / Salesforce Platform,
but multi-tenant-safe and flavor-aware.

| Capability | What a builder can do | Guardrails |
|---|---|---|
| **Custom objects** | define a new record type (name, fields, relationships to core or other custom objects), get CRUD API + list/detail screens automatically | tenant-scoped table or JSONB-backed; row limits per plan; no FK into another tenant; RLS auto-applied |
| **Custom fields** | add fields to core or custom objects (text, number, money, date, picklist, lookup, formula, rollup) | reserved-name check; indexed only via request; PII fields must be tagged (drives encryption + residency) |
| **Workflows / automations** | "when X happens, do Y" — record-triggered, scheduled, or approval flows; call core actions or a webhook | execution quotas; no direct DB; sandboxed expression language, not arbitrary code; loop/recursion guards |
| **Screens / layouts** | compose pages from design-system components into slots; per-role, per-device | design-system components only (no raw HTML/JS); a11y + RTL enforced by the components |
| **Reports / dashboards** | build queries + charts over own + permitted core data; save as a KPI pack | query-cost limits; row-level security enforced; can't export beyond own permissions |
| **Permissions** | define roles + record-level sharing rules for custom objects | cannot escalate above the tenant's own plan entitlements; audited |
| **API / webhooks** | expose a custom object or a Studio automation as a REST endpoint; register outbound webhooks | rate-limited per plan; OAuth2-scoped; appears in the tenant's own developer portal |
| **Package & share** | export a Studio configuration as an installable **flavor pack** or a private app | goes through the flavor-certification pipeline (N.6) before it can be listed publicly |

Studio changes are **metadata**, versioned per tenant, promotable dev→staging→prod within the
tenant, and never require a CyberCom deploy. This is how a systems-integrator builds
"CyberCom for Kuwaiti car dealerships" or "CyberCom for a poultry farm" without us writing a
line of code.

## N.4 Full flavor catalogue

Grouped by family. Each is `config + attribute profiles + layouts + presets` unless flagged
**[core+]** (needs a new core primitive) or **[ext]** (needs an extension app for novel logic).

### CyShop family — commerce & retail
| Flavor | One-line scope | Wave |
|---|---|---|
| RetailFlavour | general retail POS + inventory + GL | 1 |
| FiveStarRestaurantFlavour | fine dining: reservations, coursing, sommelier, service ritual, tips | 2 |
| FastFoodFlavour | QSR: combo builder, drive-thru, KDS, aggregator sync, speed-of-service | 2 |
| MultiBranchChainFlavour | franchise/chain: HQ↔branch, central menu/price, consolidated P&L, royalties | 2 |
| GroceryFlavour | weighed items, PLU, FEFO, promotions, supplier rebates | 2 |
| HypermarketFlavour **[core+]** | departments, concessions, sub-leased areas, planogram, scan-and-go | 3 |
| JewelleryCosmeticsFlavour | live metal rate, karat/purity, making-charge, AML/KYC, serial per piece | 3 |
| FashionApparelFlavour | size/colour matrix, seasons, markdown cadence, e-com + store | 3 |
| ElectronicsFlavour | serial/IMEI, warranty, trade-in, extended-warranty attach | 3 |
| HomeImprovementHardwareFlavour | trade accounts, bulk/length cut, delivery scheduling, hire desk | 3 |
| PetStoreFlavour | livestock handling, prescription diets, grooming bookings | 4 |
| ConvenienceFuelForecourtFlavour **[core+]** | pump control, wet-stock, dip reconciliation, fuel cards, C-store | 3 |

### CyMed family — health
| Flavor | One-line scope | Wave |
|---|---|---|
| ClinicFlavour (HealthFlavour) | scheduling, encounters, billing, pharmacy, NPHIES/eClaim | 1 |
| HospitalFlavour **[core+]** | wards, admissions, OT, nursing, bed management, ADT | 3 |
| LabFlavour | LIS, analyzer interfaces, home collection, DTC catalog, results portal | 3 |
| PharmacyRetailFlavour | dispensing + OTC retail, insurance POS, controlled register, compounding | 2 |
| ImagingCentreFlavour | RIS, modality worklist, DICOM archive (CyVault), sharing, teleradiology | 3 |
| TelemedicineFlavour **[ext]** | video visit, e-triage, remote e-Rx, async messaging | 3 |
| HomeHealthFlavour | visit routing, caregiver scheduling, mobile documentation | 4 |
| DentalFlavour | odontogram, perio charting, treatment plans, imaging | 4 |
| HealthGroupFlavour | multi-facility consolidation, shared MPI, group RCM | 4 |
| InsurerInterfaceFlavour **[ext]** | payer-side eligibility/pre-auth/claim adjudication interfaces | 5 |

### CyMart — marketplace
| Flavor | One-line scope | Wave |
|---|---|---|
| MarketplaceFlavour **[core+]** | vendor onboarding, seller dashboards, catalog, commission, split settlement, disputes, reviews, logistics | 2 |

### Industrial, services, public sector — universality proof
| Flavor | One-line scope | Wave |
|---|---|---|
| ManufacturingFlavour **[core+]** | BOM, routing, work orders, MES declarations, MRP, WIP costing, quality COA | 3 |
| ProcessManufacturingFlavour **[core+]** | recipe/formula, batch, co/by-products, potency, lot genealogy (cement, food, chem) | 4 |
| WholesaleDistributionFlavour | B2B pricing tiers, credit, route accounting, van sales, backorders | 2 |
| FieldServiceFacilitiesFlavour **[core+]** | asset register, preventive + reactive work orders, SLAs, technician dispatch, parts van stock | 3 |
| AutomotiveDealerServiceFlavour | vehicle unit inventory, service bays, job cards, warranty claims, parts counter | 3 |
| HospitalityHotelFlavour **[core+]** | PMS: reservations, rate plans, housekeeping, folio, night audit, channel manager | 3 |
| TravelTourOperatorFlavour **[ext]** | itinerary building, supplier contracts, booking, GDS/bedbank hooks | 4 |
| BeautySalonSpaFlavour | resource+room booking, packages, memberships, commission payroll | 3 |
| FitnessGymFlavour | memberships, class booking, access control, freeze/dunning | 3 |
| EducationTrainingFlavour **[core+]** | admissions, enrolment, timetable, gradebook, fees/financial-aid, LMS hooks | 4 |
| TelecomServiceProviderFlavour **[core+]** | subscription catalog, provisioning orders, usage rating, bill runs, dunning | 4 |
| EnergyUtilitiesFlavour **[core+]** | connection/meter registry, meter reads, tariff/determinants, bill runs, outage/work mgmt | 5 |
| GovernmentMunicipalPortalFlavour **[core+]** | citizen identity, permit/licence applications, statutory workflows, fee schedules, inspections, case management | 4 |
| RealEstatePropertyMgmtFlavour | units, leases, rent runs, maintenance, service charges | 4 |
| Logistics3PLFlavour **[core+]** | consignments, legs, hubs, proof-of-delivery, freight billing | 4 |
| AgricultureFlavour **[ext]** | fields/herds, seasons, input tracking, yield, traceability | 5 |
| ConstructionContractingFlavour **[core+]** | projects, WBS, progress billing, subcontracts, retention, plant hire | 5 |
| NonprofitNGOFlavour | fund accounting, grants, donors, programme budgets, beneficiary registry | 5 |

**~50 flavors.** Wave 1 GA: Retail + Clinic. The rest phase in per `G`, most as pure
config/Studio work once the **[core+]** primitives land.

## N.5 Stress test — six hard domains against the model

| Domain | Fits core primitives? | New core primitives (`[core+]`) | New services | Reuses unchanged |
|---|---|---|---|---|
| **Discrete manufacturing** | mostly | `BillOfMaterials`, `Routing`/`Operation`, `ProductionOrder`, `WorkCentre` | ManufacturingExecution (declarations, scrap, downtime); MRP planner | Inventory, Procurement, Finance/WIP costing, Quality, HR/shift, Scheduling |
| **Energy / water utility** | partially | `ServicePoint`/`Meter`, `MeterReading`, `Tariff`+`Determinant`, `BillingCycle` | Rating & bill-run engine; outage/asset work mgmt | Party (customer), Finance/AR, Payments, Field Service work orders, Documents (bills) |
| **Government / municipal** | partially | `CaseFile`/`Application`, `StatutoryWorkflow`, `FeeSchedule`, `Inspection` | Case-management engine; citizen-identity federation (Nafath/UAE PASS) | Party (citizen), Payments, Documents, Scheduling (inspections), Ledger (fund acct) |
| **Higher education** | partially | `Programme`/`Course`/`Section`, `Enrolment`, `AcademicRecord`, `Timetable` | Gradebook; admissions pipeline (reuses CRM); LMS integration | Party (student), Finance (fees, financial aid = pricing rules), Scheduling, Documents (transcripts) |
| **Telecom** | partially | `ServiceSubscription`, `ProvisioningOrder`, `UsageEvent`, `RatePlan` | Usage rating + bill-run; provisioning orchestration | Order (as provisioning trigger), Finance/AR, Payments, dunning, CRM |
| **Hotel (PMS)** | mostly | `RatePlan`/`Availability`, `Reservation`, `Folio`, `HousekeepingTask` | Channel-manager connector; night-audit routine | Scheduling (rooms as resources), Order/POS (F&B, spa), Finance, Inventory (minibar, amenities) |

**Pattern:** every hard domain reuses 60–80% of the core untouched, adds 3–5 first-class
nouns, and 1–2 focused services. None needs a fork. The **[core+]** nouns are a finite,
known list (~25 entities across all ~50 flavors) — that's the real "build the core once" work,
spread across `G` phases 3–5.

## N.6 Keeping "anyone can build a flavor" from becoming chaos

| Control | Rule |
|---|---|
| **Thin-flavor gate** (ADR-0003) | a flavor pack that adds a top-level model, bespoke frontend, or code branch is rejected; route the need through CDAC for a core primitive |
| **Certification tiers** | **Community** (unlisted, use-at-own-risk) · **Verified** (passed automated checks: schema-valid, no reserved names, a11y/RTL clean, quota-safe) · **Certified** (CyberCom-reviewed, listed, supported, revenue-share) |
| **Studio guardrails** | metadata only; sandboxed expression language; per-plan quotas on objects/rows/automations/API; RLS + PII tagging auto-applied; no cross-tenant references |
| **Extension apps** | run in a sandbox (own resource limits, no ambient DB/network/secrets, capability-scoped); reviewed before Marketplace listing; can be killed per tenant |
| **Core primitive additions** | RFC → CDAC → ADR → expand/contract migration; must serve ≥ 2 flavors; owned by a domain architect |
| **Deprecation** | a flavor or primitive that no live tenant uses for 2 releases is archived |

## N.7 Where the line is (honest scope)

CyberCom is the **system of record and operations** for a business — its transactions,
inventory, money, people, schedule, compliance, and customer relationships. It is **not**:

- a real-time control system (SCADA/PLC loops, sub-second machine control) — it *integrates*
  with them (OPC-UA / MQTT into `UsageEvent` / MES declarations), it doesn't replace them
- deep domain design tooling (CAD/CAM, EHR clinical-imaging workstations, GIS authoring) —
  it *references* their outputs as Documents/records
- high-frequency trading, telco packet-core, or a games backend — different beasts entirely

For those, CyberCom is the ERP the specialist system reports **into**. That boundary is a
feature: it's what keeps one platform coherent while still being the operational backbone for
a factory, a clinic, a ministry, and a corner shop at the same time.

## N.8 What this adds to the build plan

| Item | Where it lands |
|---|---|
| Canonical primitives formalised (Party/Item/Agreement/Event/Location/Resource/Schedule/Document/Ledger/Rule) | `D` data-model v1, Phase 0 |
| Studio metadata engine (custom objects/fields/workflows/layouts/reports) | Phase 1–2, a dedicated workstream — it is the platform moat |
| Extension-app sandbox + capability model | Phase 4 (with the hosting platform + developer marketplace) |
| The ~25 `[core+]` primitives | Phases 3–5, one domain cluster at a time (industrial → services → public sector) |
| Flavor certification pipeline | Phase 4–5 with the partner programme (`L.9`) |
| Full flavor catalogue as a living registry | `schemas/flavor-registry.yaml`, maintained by the flavor board |

## N.9 The complete registry and the "launch with all flavors" question

The machine-readable list of every flavor — family, wave, status, `[core+]` dependencies —
lives in **`docs/blueprint/schemas/flavor-registry.yaml`**. It is the single source of truth;
this document's N.4 table is a readable snapshot. Additions since the first draft (folded in
from the expanded objective):

| Flavor | Resolves to | Note |
|---|---|---|
| Health&WellnessFlavour | = BeautySalonSpaFlavour + FitnessGymFlavour + a wellness-retail profile, as one bundle | packaging |
| CymedAnalyticsFlavour | an **analytics KPI pack** on the health read-model, not a flavor | belongs to Analytics service |
| CymartMerchantPortalFlavour | the seller-facing surface of MarketplaceFlavour (dashboards, KPIs, payouts) | sub-surface, same flavor |
| GovernmentPortalOpsFlavour | the back-office/case-worker surface of GovernmentMunicipalPortalFlavour | sub-surface, same flavor |
| HospitalityWholesaleFlavour | = WholesaleDistributionFlavour + a hospitality-procurement profile | attribute profile |
| EducationAdminFlavour | = EducationTrainingFlavour scoped to admin/procurement/asset ops (no LMS) | config subset |

Net: no new top-level flavors — they compose from existing ones. Registry now lists **~55
named flavors / surfaces** across 6 families.

### Expert position on sequencing (this is a real disagreement worth stating)

The request is to **launch with all flavors from day one**. As the engineering owner, the
recommendation is: **the architecture supports all ~55 from day one; GA does not.**

| What ships at launch | What doesn't |
|---|---|
| The flavor **engine** + Studio + `flavor.schema.yaml` contract — any flavor is *expressible* and a partner can build one in week 1 | 55 CyberCom-built, supported, GA flavors |
| **2 GA flavors** (Retail, Clinic) — fully built, tested, compliant, referenceable | the other ~53 as "supported by CyberCom SLA" |
| **~10 Verified flavors** by end of Phase 3 (config-only, community/partner-tested) | deep verticals (`[core+]`) before their primitives land |
| The full **registry published** so the roadmap and the ecosystem are visible | marketing that implies all 55 are production-ready |

Reasoning: (1) each GA flavor carries real cost — build, test, compliance per country,
support, a runbook — and a small team that spreads across 55 delivers 55 half-products
(risk R04, the exact failure the consolidation exists to fix); (2) the moat is the *engine*
and *one canonical model*, not the count of pre-built verticals — Salesforce and Odoo both
won with a platform + a handful of first-party apps + an ecosystem for the rest; (3)
"available as config/Studio, Verified tier" is a truthful and strong market claim without
over-committing support. The registry makes the *ambition* visible; the wave columns make
the *commitment* honest. If a specific customer needs flavor #34 now, that is a
partner-delivered or paid-accelerated flavor, tracked as such.
