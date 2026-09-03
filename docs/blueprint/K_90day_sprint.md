# Section K — 90-Day Quick-Start Sprint

> Concrete week-by-week. Day 0 = kickoff. Maps to Phase 0 + the start of Phase 1 in `G`.
> Owners left generic ("Platform", "Backend", "Data", "Sec", "Product") for a small team to assign.
> Ends with 2–3 pilots warming and the flavor engine demonstrable.

## Weeks 1–2 — Reconcile, decide, baseline

### Week 1 — Repo & decisions
- [ ] **Resolve the 3 checkouts** (Platform, Data):
  - Diff `D:\cybercom` (`feat/oci-demo-deploy` @ `0e90866`, 4 ahead) vs `D:\Cybercom launch\cybercom` (`develop` @ `9060c9d`).
  - Adopt `D:\cybercom` as canonical (most recent real work). Rebase/cherry-pick the monorepo's untracked deltas (status docs, `CyEd/`, ruflo) as needed.
  - Commit, push to `origin/develop`, tag `pre-migration-baseline`.
  - Archive `D:\Cybercom launch\Cybercom-launch` (delete after snapshot). Mark the losing checkout read-only.
- [ ] Stand up **CDAC** (F.1): members, cadence, RFC + ADR templates, `CODEOWNERS` on `platform/` + core models + `docs/blueprint/`.
- [ ] Ratify this blueprint in a kickoff; open ADRs for J.1 (A1–A13).
- [ ] Founder decisions: O1 (KSA host), O2 (payroll rates), O5 (CyEd), O7 (first PSP).
- [ ] Triage **CyEd**: provenance, keep/fold/archive.

### Week 2 — Environment & contracts baseline
- [ ] **GitOps skeleton** (Platform): EKS in `me-south-1`, Argo CD, config repo (Helm + Kustomize overlays dev/staging), external secret manager. Deploy current core to staging.
- [ ] **CI hardening** (Sec): SAST + dependency scan + secret scan + image signing + SBOM, block-on-High, repo-wide (extend cymed's `security-scan.yml`).
- [ ] **API contract toolchain** (Backend): drf-spectacular → OpenAPI 3.1 published; AsyncAPI for events; contract repo + CI publish.
- [ ] **Canonical data-model v1 draft** (Data + CDAC): Tenant/Org/Branch, Catalog profiles, unified Order, Finance/GL + e-invoice fields, Scheduling. Review → approve.
- [ ] **Keycloak prod** stood up (per `GO_LIVE.md` + `infrastructure/keycloak/`); plan CyShop-JWT → CyIdentity consolidation.
- [ ] **ZATCA spike** (Backend): CSID sandbox onboarding, generate + clear one test invoice.
- [ ] **RTL workstream kickoff** (Product): adopt `next-intl`, string-extraction plan, translation vendor shortlist.

**Week 1–2 gate:** one canonical repo on `develop`; CDAC live; data-model v1 approved; staging deploys via GitOps; ZATCA sandbox clears an invoice.

## Weeks 3–6 — Core services + flavor plugin framework + Retail/Health MVP starts

### Weeks 3–4
- [ ] **Flavor engine** (Platform): promote `platform/provisioning` — multi-flavor per tenant, `VerticalFlavor` + `LayoutTemplate` models, KPI-pack + regulatory-pack concepts, `flavor.yaml` schema + validator (thin-flavor checklist enforced).
- [ ] **Unified Order aggregate** (Backend): merge CyMart order lifecycle + CyCom POS orders into one `Order` with `type`/`channel`; state-machine mapping table; keep `attributes.legacy_id`.
- [ ] **Tenant isolation hardening** (Backend + Sec): Postgres RLS via session GUC on core tables; automated cross-tenant access test suite in CI (must fail-closed); port the cross-tenant read fix from `D:\cybercom`.
- [ ] **Payments service carve-out** (Backend): extract PSP abstraction (from CyMart `payments`) into its own service; wire the chosen live regional PSP (O7); Stripe webhook HMAC verify (port from `D:\cybercom`).
- [ ] **Onboarding API** (`POST /onboarding/tenants`, Section D#1) end-to-end against staging Keycloak.

### Weeks 5–6
- [ ] **Finance: ZATCA Phase 2 clearance engine** (Backend): UBL 2.1 XML, cryptographic stamp, QR, hash chain, Fatoora clearance/reporting client, archival to CyVault. Behind flavor `regulatory: [zatca_phase2]`.
- [ ] **RetailFlavour MVP build** (Product pod, E.1): catalog + POS (web) + KDS + inventory + GL auto-posting + VAT presets + layout templates + seeded demo.
- [ ] **HealthFlavour stabilisation start** (Health pod): run CyMed test suite, fix imports/runtime, inventory what's real vs scaffold; plan shared-concern re-home (M4).
- [ ] **Event broker** (Platform): stand up (O3 decision); outbox → broker → analytics read-model + audit consumers.
- [ ] **Developer portal v1** (Backend): auth'd OpenAPI console + sandbox tenant provisioning.
- [ ] **CyShop migration M1–M2** (Data): schema-convergence migrations (additive); dry-run ETL of a CyShop prod copy into a staging canonical tenant; run D.3 reconciliation.

**Weeks 3–6 gate:** onboarding API provisions a RetailFlavour tenant < 90 s in staging; a POS sale posts GL + clears a ZATCA sandbox invoice; CyShop dry-run reconciliation passes.

## Weeks 7–10 — Pilot onboarding automation + security/governance baseline

### Weeks 7–8
- [ ] **Self-serve loop** (Product + Backend): signup → pay (live PSP) → auto-provision → first login → ring a sale, unattended, for RetailFlavour.
- [ ] **RetailFlavour hardening**: returns/exchange, discount approval, multi-branch consolidation dashboard, Arabic POS + receipts, offline-capture MVP.
- [ ] **Security baseline docs** (Sec + CDAC): STRIDE threat models for Identity, Payments, Finance/e-invoice, Order/POS; secret-manager migration complete; internal mTLS on core↔carved services.
- [ ] **Governance docs**: CDAC charter finalised, ADR set published, flavor-governance board + thin-flavor checklist in use, per-country regulatory matrix v1 (F.4).
- [ ] **Observability** (Platform): OTel tracing end-to-end, Grafana dashboards (RED + per-tenant + checkout/POS/signup SLOs), synthetic probes, PagerDuty + runbooks for top 10 alerts.

### Weeks 9–10
- [ ] **CyShop migration M3 cutover** for 1–2 friendly CyShop tenants (per-tenant freeze → delta ETL → flip → read-only source 90 days).
- [ ] **RetailFlavour → 3 JO pilot tenants** hand-provisioned + onboarded via `/setup`; live on real POS + KDS + inventory + GL.
- [ ] **HealthFlavour MVP** (Health pod, E.2): scheduling + encounter + patient billing + pharmacy dispense on canonical core; NPHIES/eClaim **sandbox** integration; PDPL-health field encryption + access audit.
- [ ] **Load test v1** (QA): P1–P3, S1–S2 thresholds from `H` against staging.
- [ ] **DR drill v1**: DB PITR restore to scratch env, integrity check.

**Weeks 7–10 gate:** self-serve Retail loop works unattended; 3 Retail pilots live; ≥ 1 CyShop tenant migrated clean; Health MVP demoable against NPHIES sandbox; SLO dashboards + runbooks in place.

## Weeks 11–12 — Pilots live, measure, iterate

- [ ] **Retail pilots: collect metrics** (E.1 KPIs): onboarding time, POS latency, offline resilience, stock accuracy, ZATCA success. Weekly review with each pilot.
- [ ] **Iterate APIs + data model** on pilot feedback; any change → CDAC → expand/contract migration.
- [ ] **Health: 1–2 clinic pilots** begin (assisted onboarding); first **multi-domain** setup (clinic + retail pharmacy on one tenant) as the cross-domain showcase.
- [ ] **AutoParts/Grocery: design spike** (Data): fitment/OE-xref/supersession model; grocery high-volume POS + scale + promotions spike. RFC to CDAC.
- [ ] **Reference customer**: convert the strongest Retail pilot to a signed reference + case study.
- [ ] **90-day readout**: metrics vs `G` Gate 2/3 evidence; decide Phase 2 scope; update `PROJECT_STATE.md`.

## 90-day success definition

- One canonical repo; CyShop migration proven (≥ 1 tenant live on canonical, dry-run gates green).
- Flavor engine provisions a multi-flavor tenant from one API call.
- RetailFlavour: **3 pilots live**, self-serve loop works, **1 reference** signed.
- HealthFlavour: MVP demoable, NPHIES sandbox integrated, 1–2 clinic pilots starting.
- **Cross-domain workflow** (clinic + pharmacy retail, one tenant, one GL) demoable end-to-end.
- ZATCA Phase 2 clearance working; security + governance baseline documented; SLOs + DR drilled.
- Real pilot metrics + pricing inputs to plan Phase 2 — no invented targets.

## Parallelisation note (ruflo / multi-agent)

This sprint fans out cleanly into parallel tracks — assign one pod/agent per lane, coordinate via CDAC:
`platform-infra` (GitOps, broker, observability) · `core-backend` (Order, isolation, onboarding API) ·
`finance-einvoice` (ZATCA) · `retail-flavor` · `health-flavor` · `data-migration` (CyShop) · `security-governance`.
Shared contracts (data model, APIs, events) are the synchronisation points — change them only through CDAC.
