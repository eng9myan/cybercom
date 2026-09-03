# Section P — Simulation, Testing & Go-Live Readiness

> How CyberCom proves itself before real customers touch it, and the gate every tenant
> passes on the way live. Extends `H` (NFR thresholds) with the *process* that verifies them.

## P.1 Simulation — synthetic worlds per flavor

Before a flavor pilots, it must survive a **simulated tenant**: a scripted synthetic business
running its full lifecycle against staging. Datasets are generated (Faker + domain rules),
deterministic (seeded), and refreshable.

| Flavor | Synthetic world | Simulated lifecycle |
|---|---|---|
| Retail / F&B | 1 brand, 5 branches, 3k SKUs, 40 staff, 90 days of trading | onboard → catalog import → daily POS + KDS + returns → nightly close → weekly payroll → monthly VAT + ZATCA/JoFotara clearance → P&L |
| Clinic (Health) | 2 clinics, 12 providers, 8k patients, 4 insurers | onboard → schedule → encounters → e-Rx + lab orders → billing (cash + insurance split) → NPHIES claim → remittance → DSAR request |
| Marketplace | 1 operator, 200 vendors, 50k listings, 5k buyers | vendor onboarding → catalog publish → orders → split payment → dispatch (CyDrive) → dispute → payout settlement → 1099-equivalent report |
| Manufacturing | 1 plant, 3 lines, 400 BOMs, 60 work centres | demand → MRP → production orders → MES declarations + scrap → WIP costing → variance analysis |
| Multi-branch chain | HQ + 30 franchised branches | central menu/price push → per-branch trading → inter-branch transfers → royalty calc → consolidated P&L |
| Hypermarket | 1 store, 12 departments, 40k SKUs, 30 lanes | high-volume POS (load) → promotions (5 concurrent) → FEFO expiry → supplier 3-way match → daily reconciliation |
| Government portal | 1 municipality, 20k citizens, 8 permit types | citizen identity → permit application → statutory workflow + inspection → fee payment → licence issue → renewal |

**Cross-domain simulation** (the ecosystem proof): one synthetic **health group** tenant runs
ClinicFlavour + PharmacyRetailFlavour + a branded RetailFlavour shop + hospital procurement —
verify one MPI, one GL, one consolidated report, consent-scoped cross-tenant referral to an
external specialist.

**Simulation harness** lives in `tools/sim/`: `sim run <flavor> --days 90 --seed 42` drives
the public API only (no test hooks), asserts invariants continuously (P.4), and emits a
report (throughput, error rate, data-quality, $ reconciled).

## P.2 Test pyramid

| Layer | Scope | Gate | Tooling |
|---|---|---|---|
| **Unit** | pure logic; tax, payroll, pricing, GL, state machines | ≥ 80% overall, ≥ 95% finance/tax/payroll/clinical-billing | pytest, coverage in CI (block-on-drop) |
| **Property-based** | invariants: GL always balances; tax = Σ line tax; stock never negative without backorder flag; e-invoice hash chain unbroken | 0 falsifying cases | Hypothesis |
| **Contract** | every provider/consumer API + event pair | build breaks on incompatibility; 2 majors kept green | schemathesis (OpenAPI), Pact-style for consumers, AsyncAPI validation |
| **Integration** | each external dependency happy + failure path, against sandboxes | all green; failure paths degrade gracefully | PSP sandboxes, ZATCA/JoFotara/NPHIES sandboxes, WPS test files |
| **E2E** | signup → provision → transact → invoice → GL, per GA flavor | green per release; Playwright, real browser, real staging stack | Playwright |
| **Simulation** | P.1 synthetic worlds | invariants hold over 90 simulated days; reconciliation balances | sim harness |
| **Load / soak** | `H` P1–P10, S1–S8 | thresholds met; no leak over 4h soak | k6 |
| **Chaos** | kill region link, PSP, broker, a pod, the DB primary | `H` A2/A6/A7 hold; auto-recovery; RPO/RTO met | quarterly game day + scripted fault injection |
| **Security** | see P.3 | no High open at GA | see P.3 |
| **UAT** | pilot customers on staging with their real data (masked) | pilot sign-off | scripted UAT scenarios per flavor |

## P.3 Security testing

| Test | Cadence | Gate |
|---|---|---|
| SAST + secret scan + dependency CVE | every PR | block on High/Critical |
| Container/image scan + SBOM + signature verify | every build | block on High; provenance attested |
| **Tenant-isolation suite** — automated cross-tenant read/write/enumerate attempts across every endpoint | every build | **100% must fail-closed**; any pass blocks the merge |
| DAST (OWASP ZAP baseline + auth scan) | nightly on staging | triage < 48h; no High to prod |
| Dependency + IaC misconfig scan | nightly | High < 7d |
| External penetration test | annual + before each GA flavor + on major surface change | all High closed and retested before GA |
| PHI/payment-path focused pentest | before Health GA / before card-capture GA | zero High; sign-off by security lead |
| Red-team / bug bounty | after GA | triage SLA; severity-based payout |
| Access review (roles, break-glass, service accounts) | quarterly | no orphan / over-privileged accounts |

OWASP ASVS L2 as the baseline standard; L3 for PHI and payment components.

## P.4 Data-integrity invariants (checked continuously in sim + prod)

- Every posted `JournalEntry` balances (Σ debits = Σ credits) per Organization.
- Trial balance per Organization per period is internally consistent and matches sub-ledgers (AR, AP, inventory, payroll).
- `Σ StockItem.on_hand × unit_cost` = inventory GL control account, per location, within rounding.
- Every `Order` grand total = Σ lines + tax − discount + charges; every `Payment` ties to an Order or Invoice; no orphans.
- E-invoice: hash chain unbroken; every cleared invoice has an archived cleared XML; sequence gaps flagged.
- Every tenant's data (rows, files, backups, analytics) resides only in its `residency_region`.
- No `ConsentGrant`-less cross-tenant read in the audit log.
- Payroll: Σ payslip net + deductions + employer contributions = batch gross totals; WPS file totals match.

A nightly **reconciliation job** runs these across all prod tenants; a failure pages and freezes the affected domain's deploys.

## P.5 Go-live readiness — per-tenant onboarding gate

Every new production tenant passes an automated checklist before it can transact:

### Platform provisioning (automated, Phase 4 hosting platform)
- [ ] Tenant record + `residency_region` + `flavor_set` created
- [ ] Keycloak realm / federation configured; admin user + forced password reset delivered
- [ ] Isolated DB schema/shard + per-tenant DEK issued; RLS verified with a probe
- [ ] Object-store prefix + signed-URL policy
- [ ] **DomainBinding**: custom domain CNAME verified, **SSL provisioned** (ACME), routing live
- [ ] Feature flags set for the tenant's flavors + plan entitlements
- [ ] Observability: per-tenant dashboards + billing meter active
- [ ] Backup policy attached; first backup taken + restore-probed

### Commercial onboarding
- [ ] Subscription active; **PSP merchant onboarding** complete (or manual-invoice mode chosen)
- [ ] For MarketplaceFlavour: operator KYC, payout account, commission schedule, dispute policy
- [ ] Tax registration captured (VAT/CR); e-invoicing mode + credentials (ZATCA CSID / JoFotara taxpayer / AE Peppol) onboarded and **sandbox-cleared a test invoice**
- [ ] Payroll country profile confirmed + WPS bank details (if HR module on)

### Data & configuration
- [ ] Chart of accounts + tax presets seeded from the flavor
- [ ] Master data imported (catalog / patients / vendors / assets) via bulk API; import reconciliation report clean
- [ ] Opening balances loaded; trial balance verified against the customer's prior system
- [ ] Layout templates + KPI dashboards applied; roles + users provisioned
- [ ] Migration (if from a legacy system) passed `D.3` data-quality gates + finance sign-off

### Verification (the customer or CS runs this)
- [ ] End-to-end smoke per flavor: e.g. Retail — provision → catalog → ring a sale → invoice clears → GL posts → KDS ticket → daily close balances
- [ ] Health — schedule → encounter → bill → claim to sandbox → portal shows it
- [ ] A restore drill from the tenant's first backup succeeds
- [ ] `CYCOM_DEV_AUTH` / any dev shim confirmed **off** (grep the running env)
- [ ] Support runbook + escalation contacts handed over

**Staged rollout:** domain-by-domain onboarding gates — a flavor opens to self-serve only
after 3 assisted tenants pass this checklist cleanly and run 30 days without a P1.

## P.6 Go-live checklist — platform-level (before opening a new flavor or region)

| Area | Must be true |
|---|---|
| Flavor | thin-flavor gate passed; seed demo + KPI pack + runbook + support playbook exist; Arabic/RTL on customer-facing screens |
| Compliance | required regulatory packs for every target country are `ready`; DPIA done for any PII/PHI; e-invoicing sandbox-cleared |
| Security | pentest of the new surface passed, all High closed; tenant-isolation suite green; threat model updated |
| NFR | `H` P/S/A thresholds met in load test; chaos game day passed; DR drill within 90 days |
| Ops | dashboards + alerts + runbooks for the new flows; on-call briefed; rollback + feature-flag kill switch tested |
| Data | migration playbook (if applicable) rehearsed; reconciliation invariants (P.4) cover the new flows |
| Commercial | pricing set; PSP + payout tested with real money in staging; support capacity planned |
| Legal | terms/DPA cover the flavor + region; data-residency contractually stated |

## P.7 Deliverables

- `tools/sim/` — simulation harness + per-flavor world generators + invariant assertions
- `tests/` — the pyramid above, wired into CI with the stated gates
- `docs/testing/QA_PLAN.md` — coverage targets, gate definitions, cadence
- `docs/security/PENTEST_SCOPE.md` + findings tracker
- `docs/operations/GOLIVE_CHECKLIST.md` — P.5 + P.6 as an executable checklist
- `docs/operations/GAMEDAY_RUNBOOK.md` — chaos scenarios + expected behaviour
- Per-flavor **readiness report** template (throughput, data-quality, reconciliation, sign-offs)
