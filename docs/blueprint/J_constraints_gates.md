# Section J — Constraints, Assumptions & Decision Gates

## J.1 Locked assumptions (ratify as ADRs in Phase 0)

| # | Assumption | Rationale | Revisit if |
|---|---|---|---|
| A1 | **Tech stack: Django + DRF (backend), Next.js 16 / React (web), React Native (mobile), PostgreSQL, Redis, OpenSearch, Kafka/Redpanda.** | Matches existing code (~120k Py LOC, CyCom + `platform/`). A rewrite in another stack is not justified. | a hard scaling wall in Django that mesh/carve-outs can't solve |
| A2 | **Cloud: AWS, Gulf regions** — `me-central-1` (UAE) + `me-south-1` (Bahrain); **KSA workloads on a sovereign region** (AWS KSA / Google Dammam / Oracle Jeddah) per PDPL + contracts. | Data residency is a sales + legal requirement in the target market. | a customer/regulator mandates a different provider; multi-cloud demand |
| A3 | **Canonical core = CyCom + `platform/`.** CyShop migrates in and is archived. CyMed keeps clinical apps, re-homes shared concerns. | CyShop is ~90% duplicate; CyMed already proves the shared-platform model. | migration reconciliation reveals CyShop data the core can't represent |
| A4 | **Modular monolith + selective service carve-outs** (Identity, Payments, Search, Files/CyVault, Workers). Not microservices-first. | Small team; premature service sprawl is the top delivery risk. | team grows past ~5 pods; a domain needs independent release cadence |
| A5 | **Flavor = config + thin pack**, not a fork. Enforced by the "thin flavor" checklist (F.1). | The entire strategy depends on new verticals being cheap. | a vertical genuinely cannot be expressed without core changes → CDAC decides |
| A6 | **Gulf-first, Jordan beachhead**, then KSA + UAE scale. | JO = home turf, easiest support/reference, bilingual-tolerant buyers. | a large anchor customer appears in KSA/UAE first |
| A7 | **Payments: local PSPs primary** (HyperPay, PayTabs, Moyasar, Tap) + **Stripe for international**. Card data never touches our servers (tokenised) → PCI **SAQ-A**. | Regional coverage + minimise PCI scope. | a PSP relationship falls through; enterprise wants direct acquiring |
| A8 | **Identity: Keycloak / CyIdentity as the single OIDC issuer.** CyShop's own JWT is deprecated. | One identity fabric is required for cross-domain + SSO. | Keycloak operational cost proves prohibitive → managed OIDC |
| A9 | **E-invoicing: build a pluggable clearance engine**; modes `SA_ZATCA` (P0), `JO_JOFOTARA`, `AE_PEPPOL`. | Each Gulf country has its own model; the shape is similar. | a country adopts a radically different model |
| A10 | **Gov-portal integrations**: ZATCA Fatoora, NPHIES (KSA health), Nafath (KSA identity), JoFotara (JO), UAE emirate eClaim + WPS. Via `cyintegrationhub` connectors. | Required for compliant operation per flavor/country. | portal API access is gated/delayed → flavor waits |
| A11 | **RTL/Arabic is a funded workstream**, `next-intl` + professional ERP-term translation, not machine translation. | Compliance-grade terminology; SA/UAE credibility. | — |
| A12 | **Orchestration: ruflo (claude-flow)** for AI-assisted delivery coordination; **daemon OFF on Windows** (native bridge OOM, #3024); CLI + user-scoped MCP only. | Verified 2026-09-04 on this machine. | move dev to Linux/WSL where the native bridge works |
| A13 | **Hosting platform (Odoo.sh-equivalent) is Phase 4**, after the first reference customers. | Building it before proven demand is premature optimisation. | manual ops becomes the bottleneck sooner than Phase 4 |

## J.2 Open decisions needing founder / CDAC input

| # | Decision | Options | Needed by |
|---|---|---|---|
| O1 | KSA sovereign hosting provider | AWS KSA region · Google Cloud Dammam · Oracle Jeddah · local partner DC | Phase 0 exit (before first KSA tenant) |
| O2 | The 2 payroll rates | SA GOSI scheme choice; UAE national contribution % (5/12.5 vs 11/15) | Phase 0 — blocks compliance claims |
| O3 | Event broker | self-managed Kafka · MSK · Redpanda Cloud | Phase 1 start |
| O4 | Pricing model specifics | per-location / per-terminal / per-provider rates; module add-on prices; marketplace take-rate; hosting tiers | Phase 2 (Retail GA) |
| O5 | CyEd (untracked education product) | fold as a flavor · keep separate · archive | Phase 0 triage |
| O6 | Repo strategy post-merge | keep monorepo · split platform as a package | Phase 0 |
| O7 | First live PSP | HyperPay · PayTabs · Moyasar | Phase 1 |
| O8 | Health go-to-market country first | JO (easier) · KSA (NPHIES, bigger) · UAE | Phase 2 |

## J.3 Go / No-Go decision gates

Each gate: **owner** decides on **evidence**; decision + rationale recorded in `PROJECT_STATE.md`.
A "No-Go" pauses that track and triggers a remediation plan — it does not kill the program.

### Gate 1 — Foundations complete (end Phase 0)
**Owner:** Head of Platform + Founder
- [ ] Single canonical repo on `develop`, pushed, tagged; other 2 checkouts archived
- [ ] CDAC operating; blueprint ratified; ADRs for J.1 filed
- [ ] Canonical data-model v1 + core API contracts approved
- [ ] Staging K8s deploys core via GitOps; secret manager in place; CI security gates on
- [ ] ZATCA sandbox returns a cleared invoice
- [ ] 2 payroll rates confirmed
- **No-Go if:** repo still divided, or ZATCA integration proves infeasible in-house within budget.

### Gate 2 — Core + flavor engine ready (end Phase 1)
**Owner:** Platform architect
- [ ] `POST /onboarding/tenants` provisions a multi-flavor tenant < 90 s p95
- [ ] POS sale → GL post → ZATCA clearance green in staging
- [ ] RLS + per-tenant DEK + internal mTLS live; cross-tenant access tests all fail
- [ ] Payments service carved; 1 live regional PSP capturing real money in staging
- [ ] CyShop dry-run passes **all** D.3 data-quality gates
- **No-Go if:** tenant isolation tests fail, or CyShop reconciliation shows unexplained financial variance.

### Gate 3 — Retail GA (Phase 2)
**Owner:** Product lead + Founder
- [ ] ≥ 3 Retail customers paying, stable 30 days, ≥ 1 signed reference
- [ ] Self-serve signup→pay→provision works unattended
- [ ] CyShop migration M3 complete; repo decommissioned
- [ ] Support first-response < 4h; < 1 P1/week; NPS ≥ 40
- **No-Go if:** self-serve loop needs manual intervention per tenant, or migration caused a customer-visible data incident.

### Gate 4 — Health GA (Phase 3)
**Owner:** Health architect + licensed clinician + Founder
- [ ] Clinical data model signed off by a licensed clinician
- [ ] NPHIES/eClaim production access; claim first-pass > 90%
- [ ] PDPL-health DPIA complete; PHI-path pentest passed with all High closed
- [ ] 2 clinic pilots stable 60 days; **zero PHI incidents**
- **No-Go if:** any PHI breach, or claim acceptance < 85%, or licensing not obtainable in the launch country.

### Gate 5 — Hosting platform / self-serve scale (Phase 4)
**Owner:** Platform/Infra + Founder
- [ ] New standard tenant: signup → paid → running instance with **zero** manual ops
- [ ] 20+ tenants operated without ops headcount growth
- [ ] Automated cohort upgrade with tested rollback
- **No-Go if:** per-tenant ops cost doesn't fall materially, or an automated upgrade caused an outage without clean rollback.

### Gate 6 — Ecosystem / monetization (Phase 5)
**Owner:** Founder + Product
- [ ] Marketplace real GMV; ≥ 3 third-party connectors published
- [ ] Pricing tiers ratified and generating expected ARPA
- [ ] Unit economics: gross margin per tenant positive after hosting + support + PSP fees
- **No-Go if:** blended gross margin per tenant is negative at target scale.

### Cross-cutting risk thresholds (any breach → CDAC review within 48h)

| Risk | Threshold |
|---|---|
| Tenant isolation | any confirmed cross-tenant data exposure → halt onboarding, incident, fix, re-test |
| Financial correctness | any GL imbalance or tax miscalculation in prod → freeze finance deploys |
| Compliance | any regulated-data residency violation → halt, notify, remediate |
| Flavor bloat | a flavor fails the thin-checklist → block release until refactored or CDAC grants a time-boxed exception |
| Delivery | a phase slips > 6 weeks → re-plan, cut scope, don't compress the gate |
