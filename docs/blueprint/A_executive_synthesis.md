# Section A — Executive Synthesis & Strategic Objective

## The objective in one paragraph

Collapse three overlapping products — **CyShop** (commerce), **CyCom** (general ERP), **CyMed** (healthcare) — into **one CyberCom platform**: a multi-tenant, API-first ERP core with a **flavor-template layer** that specialises the same engine for any industry (retail, hospitality, healthcare, auto parts, jewellery & cosmetics, groceries & hypermarkets, fuel retail, government services). One codebase, one identity fabric, one data model, one operations plane — many industry "flavors" that are configuration + a thin module pack, not forks. Gulf-first (Jordan beachhead, Saudi Arabia and UAE as the scale markets), zero-trust, cloud-native, data-resident in-region.

## Why consolidate (the case)

1. **CyShop is ~90% duplicate of CyCom** (own auth, tenants, accounting, HR, payroll, inventory) and does not sit on the shared `platform/` core. Maintaining it separately is pure cost. Its genuinely unique value (catalog, POS Device/receipt/KDS, quotations, onboarding UX) is already ported into CyCom.
2. **CyMed already proves the flavor model works** — 16 healthcare apps sitting correctly on the same shared `platform/` (identity, tenant, provisioning, events) without duplicating the core. Retail should be a flavor the same way healthcare is.
3. **The differentiator is cross-domain, not any single module.** A hospital that runs its pharmacy retail, its branded-merchandise shop, its procurement, its payroll, and its patient billing on *one* tenant with *one* ledger and *one* identity is something Odoo, Foodics, and the SAP/Oracle mid-market stack cannot do without heavy integration work. That story only exists if the products are one platform.
4. **Regional compliance is a shared tax, not per-product.** ZATCA Phase 2 e-invoicing, PDPL data residency, GOSI/gratuity payroll, WPS, Arabic/RTL — each must be built once in the core and inherited by every flavor. Three products = three times the compliance surface and three times the audit cost.

## Target shape

```
                         ┌─────────────────────────────────────────┐
                         │  Flavor packs (config + thin modules)    │
   Retail · Hospitality · Health · AutoParts · Jewelry · Grocery ·  │
   Fuel · Government   →  layout templates, module sets, tax/reg    │
                         │  presets, workflows, KPI dashboards       │
                         └───────────────────┬─────────────────────┘
                                             │  provisioning engine
                         ┌───────────────────▼─────────────────────┐
                         │  CyberCom core (shared platform/)         │
                         │  identity+SSO · tenant+billing ·          │
                         │  catalog · orders · inventory · finance/  │
                         │  GL · CRM · HR/payroll · scheduling ·     │
                         │  analytics · events · integrations ·      │
                         │  compliance · AI assist                   │
                         └───────────────────┬─────────────────────┘
                         ┌───────────────────▼─────────────────────┐
                         │  Ecosystem: payments (HyperPay/PayTabs/  │
                         │  Moyasar/Tap/Stripe) · delivery (CyDrive/ │
                         │  Talabat/Jahez) · labs · pharmacies ·     │
                         │  gov portals (Fatoora/NPHIES/Nafath) ·    │
                         │  CyMart marketplace · CyVault storage      │
                         └─────────────────────────────────────────┘
```

## What we are NOT doing

- Not a big-bang rewrite. CyCom's core + `platform/` is the foundation; CyShop folds in, CyMed re-homes its shared pieces onto the canonical core.
- Not micro-services-everything on day one. The core ships as a **modular monolith** (Django apps behind one API gateway) with a small number of independently-scaled services carved out only where load or team boundaries demand it (see C). Premature service sprawl is the failure mode.
- Not chasing Odoo on module breadth. We win a **specific buyer** (Gulf SMB / mid-market, multi-domain operators) on cross-domain workflows, localisation depth, onboarding speed, and data sovereignty.
- Not launching all flavors at once. Retail + Health first (we have the most code), AutoParts + Grocery in wave 2.

## Success signals (12–18 months)

| Signal | Target |
|---|---|
| Products merged | CyShop archived; CyCom + CyMed on one canonical core + data model |
| Reference customers live | ≥ 3 paying, ≥ 1 multi-domain (e.g. clinic + its retail pharmacy on one tenant) |
| Flavors in production | Retail + Health GA; AutoParts + Grocery in pilot |
| Onboarding time | signup → transacting in **< 1 day** self-serve for Retail; < 2 weeks assisted for Health |
| Compliance | ZATCA Phase 2 clearance live; PDPL data-residency attestation; PCI SAQ-A |
| Platform economics | per-tenant provisioning fully automated (no manual ops per customer) |
| Cross-domain proof | ≥ 1 workflow demoable end-to-end (hospital procurement via shared catalog → GL → payment) |

## The one-line strategy

**Build the core and the compliance once, express every industry as a flavor, win the Gulf multi-domain operator that no incumbent serves well, and never let the three-product split come back.**
