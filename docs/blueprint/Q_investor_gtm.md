# Section Q — Investor Readiness & Go-to-Market

> Fundraising scaffolding + the GTM engine. Numbers here are **frameworks with stated
> assumptions**, not fabricated figures — the founder fills the inputs (as in
> `BUSINESS_PLAN.md`). This section is the platform-scale layer over that document.

## Q.1 Investor deck spine

| # | Slide | Content anchor |
|---|---|---|
| 1 | Problem | Gulf/MENA multi-domain operators run 2–4 disconnected systems; incumbents are per-user-priced, slow to onboard, weak on local compliance, and can't do cross-domain. |
| 2 | Solution | One multi-tenant ERP core; every industry is a **flavor** (config + thin pack), composed per tenant; Gulf compliance built in; a developer/partner ecosystem. |
| 3 | Why now | ZATCA Phase 2 + JoFotara + UAE e-invoicing force a systems refresh across the region *now*; PDPL data-sovereignty favours a regional player; cloud + AI make guided onboarding real. |
| 4 | Product | Live demo: provision a tenant from a description in <90s → ring a sale → invoice clears with the tax authority → GL posts. Then: add a second flavor, show one ledger. |
| 5 | Market | TAM/SAM/SOM framework (Q.3). Bottom-up, per-country SMB + mid-market counts. |
| 6 | Moat | (a) canonical data model enabling cross-domain — a re-platform for any incumbent to copy; (b) regional compliance + residency; (c) flavor engine + Studio (speed); (d) partner ecosystem + marketplace network effects. |
| 7 | Business model | Q.2 — subscription (per location/terminal/provider) + module add-ons + marketplace take-rate + hosting tiers + partner-app revenue share. |
| 8 | GTM | Q.4 — land hand-held in JO → self-serve → partner-led → marketplace-pulled. |
| 9 | Traction | pilots live per flavor, reference customers, cross-domain proof, developer-portal signups, partner pipeline. |
| 10 | Competition | vertical differentiator matrix (`B` + Q.5). |
| 11 | Team | founder + key hires + advisory (regulatory, healthcare, retail). |
| 12 | Financials | Q.6 — flavor-level ARR build, unit economics, path to profitability, capital ask + use of funds. |
| 13 | Ask | round size, milestones it buys (map to `G` phase gates), 18-month plan. |

**One-page executive summary** = slides 1, 2, 3, 6, 7, 9, 12 condensed.

## Q.2 Business model — revenue lines

| Line | Mechanic | Notes |
|---|---|---|
| **Subscription** | per **billable asset** — location, POS terminal, clinical provider, vendor seat — tiered Starter/Pro/Enterprise; Commerce core bundled | maps to how the business thinks about cost; avoids Odoo's per-user penalty |
| **Module add-ons** | payroll, advanced accounting, manufacturing, CRM depth, analytics packs | introduced when buyers ask; keep launch pricing simple |
| **Flavor bundles** | industry packs priced as a bundle (e.g. "Restaurant Suite" = POS + KDS + inventory + recipe + delivery + loyalty) | packaging, not new gating |
| **Marketplace take-rate** | % of GMV on CyMart transactions + payout/settlement fee | network-effect line; scales with the ecosystem |
| **Hosting tiers** | included in subscription (managed); premium for dedicated region / higher SLA / isolated instance | the Phase-4 hosting platform makes this margin-positive |
| **Developer/partner apps** | revenue share on paid Studio flavors + extension apps in the Marketplace | Phase 5; long-tail |
| **Implementation** (partner-led) | CyberCom takes a referral cut; partners bill services | keeps our COGS low while covering high-touch verticals |
| **Payments** | interchange-plus markup or PSP referral share (optional) | only if it doesn't complicate the buyer story |

## Q.3 Market sizing framework (founder fills inputs)

```
TAM  = Σ over {JO, SA, AE, then QA/KW/BH/OM, then global}
         of (registered businesses that could run cloud ERP)
       — dominated by SA (largest economy) + AE (highest digitisation spend)

SAM  = businesses in CyberCom's live flavors × in countries with a ready
       regulatory pack × wanting cloud/subscription (not on-prem-only)
       — at launch: F&B + retail + clinics + distributors in JO/SA/AE

SOM (24 mo) = f(sales capacity, onboarding throughput, partner ramp)
            — capacity-bound, NOT demand-bound, until the hosting platform
              and partner channel exist. Model the left-most term honestly.

ARR ≈ Σ_flavor [ (net new tenants/quarter, compounding − churn)
                 × (avg billable assets/tenant × price/asset)
                 × net revenue retention ]
     + marketplace GMV × take-rate
```

Inputs to source: national SMB registries / statistics authorities per country; F&B+retail
share of SMBs; cloud-readiness %; competitor list prices (pull current, don't quote from
memory); partner pipeline conversion.

## Q.4 Go-to-market engine

| Stage | Motion | Trigger to advance |
|---|---|---|
| **0 · Reference env** | seeded demo tenants per flavor; sales shows the cross-domain "one ledger" moment | demo converts meetings to pilots |
| **1 · Land (hand-held)** | founder-led, friendly JO F&B/retail + one clinic; hand-provision; manual or single-PSP billing; high-touch onboarding | 3 paying + 1 public reference per flavor |
| **2 · Self-serve** | signup → pay → auto-provision for Retail/Auto/Grocery; content + SEO + regional ads; ZATCA/JoFotara deadline urgency | self-serve loop runs unattended; CAC < 1/3 of Y1 ACV |
| **3 · Partner-led** | recruit implementation partners (regional ERP consultancies, accountants, POS resellers); certification programme; partner portal with leads + sandbox + training | partners source > 40% of new logos |
| **4 · Marketplace-pulled** | CyMart + connector marketplace create inbound (vendors want to be where buyers are; ISVs build on the API) | marketplace GMV compounds; ecosystem apps drive retention |

**Developer program** (Phase 4–5): free sandbox tenants, tiered API access, docs + SDKs
(Python/TS), certification exam, listing in the Marketplace, revenue share. KPI: registered
developers → published flavors/apps → tenants installing them.

**Hiring plan (18 mo, indicative, founder sizes):** platform eng (2–3), flavor pods (1–2
each for Retail, Health), SRE/security (1–2), compliance/regulatory (1), founder-led sales →
first AE + CS (Phase 2), partner manager (Phase 3), DevRel (Phase 4).

## Q.5 Vertical differentiator matrix (messaging)

| Vertical | Incumbent they'd otherwise buy | CyberCom's 2–3 winning lines |
|---|---|---|
| F&B / restaurants | Foodics, POSRocket, Square | hardware-agnostic POS + live KDS on a real ERP; ZATCA/JoFotara built in; aggregator sync; multi-branch consolidation |
| General retail | Odoo, Lightspeed, local POS | days-to-value onboarding; per-terminal pricing; Arabic; POS → GL → tax in one system |
| Clinics / health | local HIS, Odoo health, paper | NPHIES/eClaim native; patient portal + billing + pharmacy on one tenant; PDPL-health from day one |
| Marketplace operators | custom builds, Mirakl (enterprise) | vendor onboarding + split settlement + disputes out of the box; regional PSP + delivery integrations |
| Auto parts / service | Tally/Excel, Epicor (heavy) | OE cross-ref + supersession + fitment as core data; multi-branch availability; B2B credit + e-invoice |
| Manufacturing (SMB) | SAP B1, Sage, spreadsheets | MES declarations + WIP costing without a 6-month implementation; integrates to shop-floor, doesn't replace it |
| Multi-branch chains | per-store POS + manual consolidation | HQ↔branch central control, royalty calc, one consolidated P&L |
| Government / municipal | bespoke gov IT | citizen-identity federation + statutory workflow engine + fee schedules + audit trail; in-country residency |

## Q.6 Financial model skeleton (build in a sheet)

| Block | Drivers |
|---|---|
| **Revenue** | per-flavor: tenants, billable assets/tenant, price/asset, ramp curve, churn, NRR; + marketplace GMV × take-rate; + hosting premium; + partner-app share |
| **COGS** | cloud infra/tenant (falls with the hosting platform), PSP fees, support cost/tenant (falls as self-serve matures), e-invoicing/gov-portal per-doc fees, data-residency premium for KSA sovereign |
| **Gross margin** | target > 70% blended by Phase 5; per-tenant GM positive by end of Phase 2 for Retail |
| **S&M** | founder-led (low cash, high time) → AE + CS + partner manager + ads; CAC per channel |
| **R&D** | the hiring plan (Q.4); the `[core+]` primitive backlog is the big multi-quarter spend |
| **G&A** | compliance/legal (per-country), certifications (ISO 27001, SOC 2), finance |
| **Capital ask** | funds `G` phases 0–4 to the point of self-serve + hosting platform + 2 flavors GA + first cross-domain reference; use-of-funds mapped to phase gates |
| **Break-even** | function of self-serve conversion + partner ramp + hosting-platform margin unlock; model conservative (capacity-bound) and don't hockey-stick before Phase 4 |
| **Sensitivity** | vary: onboarding throughput, churn, KSA-region cost, partner conversion, ZATCA deadline-driven demand pull-forward |

## Q.7 Investor risk-mitigation narrative (pair with `M`)

| Investor concern | Answer |
|---|---|
| "Too broad — 50 flavors is unfocused" | GA is 2 flavors; the rest are config on one core; the thin-flavor gate + certification tiers prevent sprawl; partners build the long tail. |
| "Incumbents will crush you" | Not competing on breadth; winning the cross-domain Gulf operator no incumbent serves; compliance + residency + onboarding are the wedge; `B` shows the review-backed gaps. |
| "Regulatory risk (health, payments, tax)" | Compliance built into the core once, not per flavor; ZATCA/JoFotara/NPHIES sandbox-proven before GA; SAQ-A keeps card data off our systems; regulatory pack gates flavor activation per country. |
| "Execution risk with a small team" | Ruthless phasing (`G`); one flavor at a time; AI-assisted delivery; partner channel offloads high-touch verticals; gates cut scope, never slip. |
| "Migration / consolidation risk" | Already de-risked: checkout reconciliation done, buildout committed + pushed; CyShop migration has dry-run + data-quality gates + rollback (`D.3`). |
| "Where's the moat in 3 years" | Canonical data model (cross-domain), regional compliance depth, the flavor/Studio engine, and the partner + marketplace network effects — each compounding. |

## Q.8 Deliverables

- Investor deck outline (Q.1) → filled deck
- One-page executive summary
- Financial model spreadsheet (Q.6 skeleton → populated with founder inputs)
- Vertical differentiator matrix (Q.5) as a standalone messaging asset
- GTM playbook (Q.4) + partner-programme one-pager + developer-program overview
- 18-month hiring plan mapped to `G` phases
