# Section M — Risk Register

> Living document. Owner reviews monthly; CDAC reviews Critical/High. Score = Likelihood (1–5) × Impact (1–5).
> Status: Open / Mitigating / Accepted / Closed.

## Critical & High (score ≥ 12)

| ID | Risk | L | I | Score | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|
| R01 | **3 divergent checkouts** — real work in `D:\cybercom` not committed; commits PROJECT_STATE cited didn't exist on the pushed branch; ~195 + ~135 uncommitted files. | 5 | 5 | 25 | **CLOSED 2026-09-04.** Adopted `D:\cybercom` `feat/oci-demo-deploy` as canonical; committed ~760 outstanding files (`7848b40`) + this blueprint; `develop` fast-forwarded and pushed to `origin/develop`. Other two checkouts marked read-only. Residual: cherry-pick any unique audit docs from the monorepo checkout; delete `Cybercom-launch`. | Platform + Data | Closed |
| R02 | **ZATCA Phase 2 infeasible in-house / on time** — net-new, cryptographic, regulator-certified, deadline already passed. Blocks every KSA tenant. | 3 | 5 | 15 | Phase 0 spike + CSID sandbox; fallback = certified Solution Provider partner or a compliant middleware vendor. Gate 1 evidence. | Finance pod | Open |
| R03 | **Tenant isolation defect** — cross-tenant data exposure. | 3 | 5 | 15→8 | Defence-in-depth: **write side** covered by `TenantScopedMixin.save()` autofill (2026-09-04); **RLS DDL + `apply_rls` command + session-GUC middleware wiring shipped** (behind `RLS_ENFORCED`, fail-closed policy, 2026-09-04) — flip the flag in staging + run the DDL + verify to enforce. Still to do: per-tenant DEK for PII/PHI columns, object-store prefix, automated cross-tenant access suite in CI, pentest before each GA. Any confirmed exposure → halt onboarding. | Backend + Sec | Mitigating |
| R04 | **Flavor bloat** — verticals accrete bespoke models/frontends → back to 3 products' worth of maintenance. The whole strategy fails silently. | 4 | 4 | 16 | "Thin flavor" checklist as a hard release gate; CDAC + flavor board review; `CODEOWNERS` on core models; time-boxed exceptions only. | CDAC | Open |
| R05 | **CyMed runtime unverified** — ~68k LOC, never run this cycle. | 4 | 4 | 16→2 | **VERIFIED + HARDENED 2026-09-04**: `check`/migrations clean, **pytest 486/23/6 → 515/0**. Fixed: `requests` dep, payments `tenant_id` (3× real bugs) + half-payment logic, rcm test infra, hospital 429s (ratelimit off in test), celery-eager. The nphies + payments tenant-scoping gaps closed by `TenantScopedMixin.save()` auto-fill (`specs/canonical-data-model-v1.md` §2.2). | Health pod | Closed |
| R06 | **PHI / health-data incident** — breach, mis-disclosure, residency violation. | 2 | 5 | 10→5 | **Field-encryption infra + first columns shipped** (`EncryptedText`, per-tenant AES-256-GCM DEK, blind-index lookup, PII registry + `dump_pii_map`, 2026-09-04). Encrypted: CyMed `Patient.national_id`/`passport_number`, `PatientContact.telecom_value`, `PatientAddress` lines; CyCom `Partner.iban`, `Employee.email`/`phone`. Still: clinical free-text (`notes`/diagnoses — needs search-impact review), access audit 100%, consent enforcement, in-region storage, DPIA per flavor, PHI-path pentest before Health GA, zero-incident gate. | Sec + Health | Mitigating |
| R07 | **Small-team capacity** — blueprint spans ~7 parallel lanes; realistic team is far smaller. Everything slips or quality drops. | 4 | 4 | 16 | Ruthless sequencing (Retail first, one flavor at a time); AI-assisted delivery (ruflo); cut scope not gates; hire/contract against Phase 2 revenue. Phase slip > 6 weeks → re-plan. | Founder | Mitigating |
| R08 | **Payments not live** — no gateway wired; blocks paid self-serve. | 3 | 4 | 12 | Manual invoice for first hand-held customers; wire 1 PSP in Phase 1 (seam exists, low technical risk). | Payments pod | Mitigating |
| R09 | **Migration data loss / financial variance** — CyShop/CyMed cutover corrupts ledgers or drops orders. | 3 | 5 | 15 | Dry-run into staging first; D.3 data-quality gates (trial-balance equality, valuation equality, order checksums) must pass; short freeze + delta not dual-write; source kept read-only 90 days; finance sign-off per cutover. | Data + Finance | Open |

## Medium (score 6–11)

| ID | Risk | L | I | Score | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|
| R10 | **RTL/Arabic under-delivered** — "foundation" is greenfield; SA/UAE credibility needs it. | 4 | 3 | 12 | Funded workstream from Phase 0; `next-intl`; professional ERP-term translation; lead in JO (bilingual-tolerant) first. | Product | Mitigating |
| R11 | **Partner API access gated/slow** — Talabat, NPHIES, Nafath, WPS banks require approval; timelines outside our control. | 4 | 3 | 12 | Start applications in Phase 0/1; flavor won't activate a country without its regulatory pack `ready`; manual fallback where legal. | Platform pod | Open |
| R12 | **Keycloak operational cost/complexity** — self-run OIDC at multi-tenant scale is heavy. | 3 | 3 | 9 | Evaluate managed OIDC as a fallback (J.1 A8 revisit trigger); invest in Keycloak runbooks + HA early. | Platform pod | Accepted |
| R13 | **KSA sovereign-region choice delays** — provider decision (O1) blocks first KSA tenant. | 3 | 3 | 9 | Decide by Phase 0 exit; JO/UAE regions unblock pilots meanwhile. | Founder | Open |
| R14 | **Odoo/SAP competitive response / channel lock** — incumbents cut price or lean on partners. | 3 | 3 | 9 | Compete on cross-domain + localisation + onboarding, not price; build own partner programme; tight ICP. | Product | Accepted |
| R15 | **Modular monolith hits a scaling wall** — a domain needs independent scale/release before we're ready to carve it. | 2 | 4 | 8 | Clean app boundaries + events from day one make carve-out cheap; carve Identity/Payments/Search/Files/Workers already planned. | Platform architect | Mitigating |
| R16 | **Financial correctness bug in prod** — GL imbalance, tax miscalc. | 2 | 5 | 10 | Property-based tests (GL always balances, tax = Σ line tax); immutable posted entries; freeze finance deploys on any prod imbalance. | Finance pod | Mitigating |
| R17 | **Payroll rate error** — 2 flagged rates unconfirmed; compliance mis-statement is a legal/trust risk. | 3 | 4 | 12 | Confirm SA scheme + UAE national % in Phase 0 before any compliance claim; cite sources; legal review. | HR pod + Founder | Open |
| R18 | **CyEd unknown** — 7th untracked product, unknown provenance/licensing/data. | 3 | 2 | 6 | Phase 0 triage: fold as flavor / keep separate / archive (decision O5). | Founder | Open |
| R19 | **Developer-portal / API abuse** — public API → scraping, quota abuse, credential leaks. | 3 | 3 | 9 | Rate-limit tiers, OAuth2 client mgmt, per-key quotas, anomaly detection, sandbox isolation. | Backend | Open |
| R20 | **Vendor lock-in (AWS)** — deep managed-service use. | 2 | 3 | 6 | Kubernetes + OSS-compatible services (Postgres, Redis, Kafka, OpenSearch) keep portability; accept for speed now. | Platform architect | Accepted |
| R21 | **Observability gaps at launch** — flying blind on a multi-tenant prod. | 3 | 4 | 12 | OTel + dashboards + synthetic probes + runbooks are Phase 0–1 deliverables, gated. | Platform pod | Mitigating |
| R22 | **Upgrade / migration breakage** (the Odoo failure mode) — a schema change breaks tenants. | 3 | 4 | 12 | Strict expand/contract; never breaking-migration + dependent-code in one deploy; canary per tenant cohort; tested rollback. | Platform architect | Mitigating |

## Low (score ≤ 5) — monitor

| ID | Risk | Mitigation |
|---|---|---|
| R23 | Ruflo daemon token spend / native-bridge instability on Windows | daemon OFF; CLI-only; move dev to WSL/Linux if it matters |
| R24 | Design-system scope creep | one component library, layout-template slots only, no per-flavor CSS |
| R25 | Documentation drift (blueprint vs code) | `docs/blueprint/` in `CODEOWNERS`; update on every contract change; quarterly reconcile |
| R26 | GraphQL over-fetch / N+1 | persisted queries only in prod; DataLoader; query cost limits |

## Risk themes → program responses

| Theme | Response |
|---|---|
| **The merge (R01, R09)** | is the single highest risk. Nothing else starts clean until Week 1 is done right. |
| **Compliance is existential (R02, R06, R17)** | ZATCA + PHI + payroll rates gate GA. Build compliance into the core, not per flavor. |
| **The strategy can fail silently (R04)** | flavor bloat looks like progress. The thin-flavor gate is non-negotiable. |
| **Capacity is the constant constraint (R07)** | sequence hard, one flavor at a time, cut scope before gates. |
