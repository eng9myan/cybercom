# Section H — Non-Functional Requirements Checklist

> Every requirement has a **testable threshold** and a **verification method**. Tracked in the
> QA plan; gates in `G` reference these. Baseline load assumption for launch: 200 tenants,
> 2k concurrent POS terminals, 5M orders/month, peak 50 orders/s.

## Performance & latency

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| P1 | POS "ring a sale" (add line → total) | p95 < 400 ms, p99 < 800 ms | k6 load test against staging, synthetic probe in prod |
| P2 | Checkout / order confirm (incl. payment capture, GL post) | p95 < 2.5 s (excl. PSP 3-DS), p99 < 5 s | k6 scenario, trace analysis |
| P3 | ZATCA invoice clearance round-trip | p95 < 10 s, p99 < 20 s (Fatoora-bound) | integration test w/ sandbox, prod metric |
| P4 | Catalog search / parts lookup | p95 < 300 ms at 10k SKUs | OpenSearch benchmark |
| P5 | GraphQL portal dashboard load | p95 < 1.5 s | Lighthouse + API timing |
| P6 | Tenant provisioning (onboarding API → usable tenant) | p95 < 90 s | end-to-end timed test per release |
| P7 | API gateway overhead | < 15 ms added p95 | gateway metrics |
| P8 | Report / analytics query (standard KPI pack) | p95 < 3 s | read-model benchmark |
| P9 | Payroll batch (500 employees, calculate) | < 60 s | timed test |
| P10 | Bulk catalog import | ≥ 50 products/s sustained | job benchmark |

## Scalability

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| S1 | Horizontal scale of core API | linear to 10× baseline RPS by adding pods, no code change | load test at 1×/3×/10× |
| S2 | Order throughput | sustain 200 orders/s peak, 500 orders/s burst 5 min | soak + spike test |
| S3 | Tenant density | 1000 tenants per cluster with isolation intact | scale test + RLS verification |
| S4 | Catalog size | 100k SKUs/tenant, 5M SKUs/cluster | data-volume test |
| S5 | Event pipeline | 5k events/s, consumer lag < 30 s under peak | broker load test |
| S6 | Async workers | queue drains within 2× enqueue rate; autoscale (KEDA) on depth | queue soak test |
| S7 | DB | read replicas for analytics; primary < 70% CPU at peak; partition hot tables (Order, StockMove, AuditEvent, DomainEvent) | capacity test, `EXPLAIN` review |
| S8 | Multi-region | add a region as a config+deploy operation, < 1 day | runbook dry-run |

## Availability & reliability

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| A1 | Core API uptime | 99.9% monthly (≤ 43 min/mo) at launch; 99.95% by Phase 4 | SLO dashboard, external monitor |
| A2 | POS availability (incl. offline mode) | 99.99% effective — sales never blocked by cloud outage | chaos test: kill cloud link, verify offline capture + sync |
| A3 | Payment capture success | ≥ 99.5% (excl. genuine declines) | PSP metrics, reconciliation |
| A4 | Checkout journey SLO | 99.5% success | synthetic + real-user monitoring |
| A5 | Error budget policy | burn > 2% in 1h or 5% in 6h → freeze feature deploys, page | Alertmanager burn-rate rules |
| A6 | Graceful degradation | PSP/gov-portal/aggregator down → queue + retry, core stays up; invoice clears async | dependency-failure test |
| A7 | Zero-downtime deploys | blue/green core, canary risky changes, auto-rollback on SLO breach | every release; game day |

## Disaster recovery & backup

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| D1 | RPO | ≤ 5 min (DB PITR + streaming replica) | restore drill |
| D2 | RTO | ≤ 1 h (warm standby in-region) | quarterly failover drill |
| D3 | Backup cadence | DB continuous PITR + hourly snapshot; object store versioned + cross-AZ; config in git | backup monitor |
| D4 | Backup retention | 35 days operational; 7 years financial docs (WORM); per-reg for health | retention audit |
| D5 | Backup encryption + residency | AES-256, in-region only, restore-tested | drill + region check |
| D6 | Restore verification | automated monthly restore to scratch env + integrity check | CI job |
| D7 | Region isolation for regulated tenants | no failover across residency boundary | DR plan review |

## Security hardening (thresholds — controls in F.2)

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| SEC1 | CI security gates | block on any High/Critical SAST, dependency CVE, or leaked secret | pipeline enforced |
| SEC2 | Patch SLA | Critical vuln patched < 48h, High < 7d | vuln tracker |
| SEC3 | Pentest | annual external + per-major on changed surface; all High closed before GA | report + retest |
| SEC4 | Tenant isolation test | automated cross-tenant access attempts in CI (must all fail) | isolation test suite every build |
| SEC5 | Encryption coverage | 100% of PII/PHI columns field-encrypted; 0 plaintext secrets in images/git | scanner + audit |
| SEC6 | Audit completeness | 100% of auth/finance/PHI/config events logged, tamper-evident | audit-log integrity check |
| SEC7 | MFA enforcement | 100% of admin/finance/PHI roles | policy report |
| SEC8 | Incident response | detect < 15 min (critical), contain < 1h, PDPL regulator notice < 72h | tabletop + real-incident review |

## Observability & operations

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| O1 | Trace coverage | 100% of API requests traced end-to-end incl. external calls | trace sampling audit |
| O2 | Log correlation | every log line carries trace-id + hashed tenant-id | log schema lint |
| O3 | Alert quality | < 5% false-positive rate; every alert has a runbook | monthly alert review |
| O4 | MTTA / MTTR | MTTA < 10 min (P1), MTTR < 2h (P1) | incident metrics |
| O5 | Dashboards | per-service RED + per-tenant + business KPIs, one click from alert | dashboard review |
| O6 | Synthetic monitoring | checkout, POS, signup, ZATCA clearance probed every 60 s from 2 regions | probe config |
| O7 | Capacity review | monthly; forecast 3 months ahead; headroom ≥ 40% at peak | capacity report |

## Testing & QA standards

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| Q1 | Unit coverage | ≥ 80% on core services + finance/tax/payroll (safety-critical: ≥ 95%) | coverage gate in CI |
| Q2 | Contract tests | every API consumer/provider pair; break the build on incompatibility | Pact/schema tests |
| Q3 | Integration tests | happy + failure paths for every external dependency (PSP, Fatoora, NPHIES, WPS) against sandboxes | CI integration suite |
| Q4 | E2E | signup→provision→sale→invoice→GL green per release for each GA flavor | Playwright suite |
| Q5 | Migration tests | D.3 data-quality gates automated; run on every migration script change | migration test harness |
| Q6 | Load/soak | before each GA and quarterly; P1–P10 + S1–S8 thresholds | k6 + report |
| Q7 | Chaos | quarterly game day: kill region link, PSP, broker, a pod; verify A2/A6/A7 | game-day report |
| Q8 | Financial correctness | property-based tests: GL always balances; tax = sum of line tax; no negative stock without backorder flag | test suite |
| Q9 | Regression | 0 known P1 regressions ship; P2 regressions triaged in 48h | release checklist |

## Accessibility & UX performance

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| U1 | WCAG | 2.2 AA on customer-facing + high-use operator screens | axe CI + manual audit |
| U2 | RTL | full mirroring, Arabic-Indic numeral option, logical CSS properties, no clipped text | RTL visual-regression suite |
| U3 | Web vitals (portals) | LCP < 2.5s, INP < 200ms, CLS < 0.1 (p75, 4G) | Lighthouse CI, RUM |
| U4 | POS on low-end Android | usable on a 2GB-RAM tablet; cold start < 4s; 60fps scroll | device-lab test |
| U5 | Offline UX | clear online/offline indicator; no data loss; conflict resolution defined | offline test script |
| U6 | Localisation completeness | 100% of user-facing strings externalised; 0 hardcoded English in GA flavors | i18n lint |
| U7 | Keyboard + scanner | all POS/counter flows completable without a mouse | task test |

## Data & compliance NFRs

| # | Requirement | Threshold | Verify |
|---|---|---|---|
| C1 | Residency | regulated-category data never leaves the tenant's region (logs, backups, analytics included) | data-flow audit per release |
| C2 | DSAR turnaround | export/delete request fulfilled < 30 days, automated where possible | DSAR workflow test |
| C3 | Consent | no cross-domain data access without an active ConsentGrant; 100% enforced | policy-engine test |
| C4 | E-invoice integrity | hash chain unbroken; every cleared invoice archived immutably 7y | chain-verify job |
| C5 | Audit retention | financial 7y WORM; health per-reg; access logs 1y min | retention monitor |
