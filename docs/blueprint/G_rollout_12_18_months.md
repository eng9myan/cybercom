# Section G — 12–18 Month Rollout Plan

> Phased, gated. Month 0 = program kickoff. Assumes a small team (see risks in `BUSINESS_PLAN.md`):
> scale sales only after self-serve + hosting automation exist. Each phase has an **exit gate**;
> do not start the next phase until the gate passes.

## Milestone chart

```
Month:      0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18
Phase 0  [==========]  Foundations
Phase 1       [===============]  Canonical core + flavor engine
Phase 2            [====================]  Retail GA + Health pilot
Phase 3                      [====================]  Health GA + AutoParts/Grocery pilot
Phase 4                                [==================]  Hosting platform + self-serve scale
Phase 5                                          [==================]  Ecosystem + marketplace + monetization
Phase 6                                                    [============]  Wave-3 flavors + expansion
Phase 7                                                              [======>  Global localization packs
```

## Phase 0 — Foundations (Months 0–2)

**Goal:** one repo, one truth, decisions locked, team + platform bootstrapped.

- Reconcile the 3 checkouts → canonical `develop`, pushed, tagged `pre-migration` (`K` Week 1).
- Stand up CDAC (F.1); ratify this blueprint; open ADRs for the locked decisions (`J`).
- Canonical data-model v1 defined; API contract repo + OpenAPI/AsyncAPI toolchain; event schema registry.
- K8s + GitOps skeleton in the Gulf region; secret manager; CI hardening (SAST/scan/sign repo-wide).
- Keycloak prod stood up; CyShop JWT → CyIdentity consolidation plan.
- ZATCA Phase 2: spike + CSID sandbox onboarding.
- RTL/i18n workstream kicked off (next-intl adoption, string extraction plan).
- Confirm the 2 payroll rates (SA scheme, UAE national %).

**Exit gate:** single canonical repo on `develop`; CDAC operating; data-model v1 + core API contracts approved; staging cluster deploys the current core via GitOps; ZATCA sandbox returns a cleared invoice.

## Phase 1 — Canonical core + flavor engine (Months 1.5–5)

**Goal:** the platform can provision a multi-flavor tenant on one data model.

- Promote `platform/provisioning` to the **flavor engine** (multi-flavor per tenant, layout templates, KPI packs, regulatory packs).
- Canonical entities live: Tenant/Org/Branch, Catalog profiles, unified **Order** aggregate (merge CyMart order lifecycle + CyCom POS), Finance/GL with **ZATCA Phase 2 clearance**, Scheduling as shared service.
- Tenant isolation hardened: Postgres RLS + per-tenant DEK + internal mTLS.
- Payments service carved out (PCI isolation); one live regional PSP (HyperPay or PayTabs).
- Event broker upgrade + outbox → broker → analytics read-model + audit consumers.
- Developer portal v1 (auth'd OpenAPI console, sandbox tenants).
- **CyShop migration M1–M2** (schema convergence + dry-run).

**Exit gate:** `POST /onboarding/tenants` provisions a RetailFlavour tenant end-to-end (Keycloak realm, seeded catalog, tax presets, layout templates) in < 90 s p95; a POS sale posts GL + clears a ZATCA invoice in staging; CyShop dry-run reconciliation passes all D.3 data-quality gates.

## Phase 2 — Retail GA + Health pilot (Months 3–7)

**Goal:** first revenue, first reference, Health in the field.

- **RetailFlavour MVP** (E.1) → 3 JO F&B/retail pilots → GA.
- **CyShop migration M3 cutover** (per-tenant); CyShop repo frozen read-only.
- Self-serve signup → pay → provision open to a controlled prospect set.
- Loyalty/promotions + one delivery-aggregator connector (Talabat or Jahez).
- **HealthFlavour MVP** (E.2): CyMed apps stabilised + re-homed shared concerns (M4 start); NPHIES/eClaim sandbox; 2 clinic pilots begin.
- Analytics: per-flavor KPI dashboards live.
- ISO 27001 program started.

**Exit gate:** ≥ 3 Retail customers paying and stable 30 days, ≥ 1 reference; self-serve loop works unattended for a new Retail tenant; CyShop fully migrated + decommissioned; 2 Health pilots live with > 90% claim first-pass.

## Phase 3 — Health GA + AutoParts/Grocery pilot (Months 6–11)

- HealthFlavour → GA (clinic tier); hospital add-ons in progress.
- **AutoPartsFlavour MVP** (E.3): fitment/xref/supersession model; 2 distributor pilots.
- **GroceryFlavour MVP** (E.4): high-volume POS + scale + promotions; 2 pilots.
- First **multi-domain reference** live (e.g. clinic + retail pharmacy on one tenant).
- CyMed M4 complete (shared concerns on canonical core); clinical apps as HealthFlavour modules.
- UAE market entry: residency region, WPS SIF, e-invoicing mode `AE_PEPPOL` monitoring.
- Second + third PSP; Stripe for international.

**Exit gate:** Health GA with ≥ 2 paying clinics; AutoParts + Grocery each ≥ 2 pilots stable 45 days; 1 cross-domain workflow demoable end-to-end; SOC 2 Type II observation window started.

## Phase 4 — Hosting platform + self-serve scale (Months 8–13)

**Goal:** remove manual ops per customer — the scaling unlock.

- **Odoo.sh-equivalent hosting platform**: API/one-click tenant provisioning into isolated, operated instances; environment management (staging/prod per tenant where needed); automated upgrades (expand/contract + canary per tenant cohort); automated backup + restore; per-tenant observability + billing metering.
- Self-serve GA for Retail + AutoParts + Grocery; assisted-only for Health.
- Provisioning throughput target: 0 human-minutes per standard tenant.
- Partner onboarding portal (resellers/implementers).

**Exit gate:** a new standard tenant goes signup → paid → running instance with **zero** manual ops; 20+ tenants operated without ops headcount growth; upgrade of a tenant cohort runs automated with rollback tested.

## Phase 5 — Ecosystem, marketplace, monetization (Months 11–16)

- CyMart marketplace GA: cross-tenant selling, commission, settlement, CyDrive + aggregator fulfilment.
- Ecosystem connectors hardened: PSPs, delivery, labs, pharmacies, insurers, gov portals (Fatoora/NPHIES/Nafath/JoFotara).
- App/connector marketplace on the developer portal (revenue share).
- Monetization: finalise per-location/terminal/provider pricing tiers; module add-ons; marketplace take-rate; hosting tiers.
- Enterprise features: advanced SSO, custom SLAs, dedicated regions, audit exports.

**Exit gate:** marketplace has real GMV; ≥ 3 third-party connectors published; ARR mix diversified beyond seat subscriptions.

## Phase 6 — Wave-3 flavors + regional expansion (Months 14–18)

- **JewelryCosmeticsFlavour** (live rate feed, purity, AML/KYC), **FuelStationFlavour** (wet-stock, pumps, dip), **GovernmentPortalFlavour** (citizen services, gov-portal identity).
- Hospitality full depth (PMS-grade for hotels).
- Deeper KSA/UAE penetration; Qatar/Kuwait/Bahrain/Oman assessment.
- Enterprise sales playbook + named-account motion.

**Exit gate:** ≥ 1 of the wave-3 flavors in pilot; a GCC market beyond JO/SA/UAE scoped with a regulatory pack.

## Phase 7 — Global localization packs (Months 17–18+)

- Localization SDK: a new country = a pack (tax engine config, e-invoicing connector, payroll profile, locale, PSPs) with no core changes.
- Advanced AI/automation: forecasting, auto-replenishment, anomaly detection, NL analytics, agentic ops assist — under existing AI governance.
- Target: 2 non-Gulf markets scoped.

## Gating criteria summary

| Gate | Owner | Evidence |
|---|---|---|
| Foundations | Head of Platform | canonical repo, CDAC minutes, approved contracts, GitOps deploy, ZATCA sandbox pass |
| Core + flavor engine | Platform architect | onboarding API demo, staging POS→GL→clearance, CyShop dry-run report |
| Retail GA | Product lead | 3 paying + reference, self-serve loop, migration complete |
| Health GA | Health architect + clinician | 2 paying clinics, claim acceptance, zero PHI incidents, DPIA, pentest |
| Hosting platform | Platform/Infra | zero-ops tenant provisioning, cohort upgrade w/ rollback |
| Ecosystem/monetization | Founder + Product | marketplace GMV, connector count, pricing ratified |
| Wave-3 / expansion | CDAC | flavor thin-checklist pass, new-market regulatory pack ready |
