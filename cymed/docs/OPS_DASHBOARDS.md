# Operations Dashboards — SLOs & Business KPIs

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of SRE / Head of Product Ops — TBD>` |
| Review cadence | Quarterly |

---

## 0. Purpose

Single reference for what CyMed measures, why, at what target, and where the dashboard lives. Grafana is the primary visualisation surface; dashboards are provisioned as code from `ops/grafana/` (to be built). Product KPIs surface both in Grafana (from the platform data warehouse) and in an executive-focused view.

## 1. SLOs — Reliability

Every SLO defines: **Metric**, **Definition**, **Target (window)**, **Error budget policy**, **Alert**, and **Dashboard link**.

### 1.1 Availability

- **Metric**: `sli:api:availability`
- **Definition**: 1 − (5xx responses on `/api/*` / total responses), per 1-minute bucket, from the API gateway logs; excludes explicit maintenance windows.
- **Target**: 99.9% rolling 28-day (Standard); 99.95% rolling 28-day (Enterprise).
- **Error budget policy**: freezing feature deploys when < 25% budget remaining in the current window.
- **Alerts**: fast-burn (2%/1h) → SEV2; slow-burn (10%/6h) → SEV3.
- **Dashboard**: Grafana → `Reliability / API Availability` (to be built at `ops/grafana/reliability/availability.json`).

### 1.2 Latency

- **Metric**: `sli:api:latency_p95`
- **Definition**: p95 response latency for `/api/*` endpoints, excluding known long-running endpoints (bulk export, DICOM upload); measured server-side.
- **Target**: p95 ≤ 400 ms and p99 ≤ 1200 ms over rolling 28 days.
- **Alerts**: p95 > 800 ms sustained 15 min → SEV3; > 1500 ms sustained 5 min → SEV2.
- **Dashboard**: `Reliability / API Latency`.

### 1.3 Error rate

- **Metric**: `sli:api:error_rate`
- **Definition**: proportion of 5xx + upstream-timeout responses on `/api/*`, per minute.
- **Target**: ≤ 0.5% rolling 24 h.
- **Alerts**: > 1% for 5 min → SEV3; > 5% for 2 min → SEV1.
- **Dashboard**: `Reliability / API Error Rate`.

### 1.4 Job success rate

- **Metric**: `sli:jobs:success`
- **Definition**: successful async job completions / total attempted, per queue (billing, claims, DICOM ingress, export, notifications).
- **Target**: ≥ 99.5% per queue rolling 24 h.
- **Alerts**: per-queue burn > 2× baseline → SEV3.
- **Dashboard**: `Reliability / Job Health`.

### 1.5 Data freshness

- **Metric**: `sli:pipeline:freshness_p95`
- **Definition**: max event-to-availability lag for warehouse tables serving KPIs.
- **Target**: p95 ≤ 15 minutes.
- **Alerts**: lag > 30 min sustained 15 min → SEV3.
- **Dashboard**: `Reliability / Pipeline Freshness`.

### 1.6 Backup and DR

- **Metric**: `sli:backup:success_daily`, `sli:dr:rto_verified`.
- **Definition**: daily backup completion, weekly PITR restore verification, quarterly regional-failover drill.
- **Target**: 100% backups on schedule; PITR RPO ≤ 15 min; RTO ≤ 4 h (Enterprise).
- **Alerts**: missed backup → SEV2; failed PITR verification → SEV2.
- **Dashboard**: `Reliability / Backup & DR`.

## 2. Business KPIs

### 2.1 Adoption

- **Onboarded tenants** — count of production tenants live in period.
- **Active tenants** — tenants with ≥ 1 signed encounter or dispensed script or reported study in period.
- **Time-to-first-value** — median days from contract signature to first signed encounter.
- Target thresholds per plan-year, set in the OKR system; dashboard shows trend + target.

### 2.2 Daily Active Users (DAU)

- **DAU** = distinct authenticated users with ≥ 1 event per role in a day.
- **DAU/MAU** ratio as stickiness proxy.
- **Weekly retention cohorts**.
- Dashboard: `Product / Adoption`.

### 2.3 Clinical throughput

- **Encounters signed / day** — per facility, per specialty.
- **e-Prescriptions issued / day** — per facility.
- **Dispenses / day** — per pharmacy.
- **Imaging studies acquired / day** — per modality.
- **Lab tests resulted / day** — per lab.
- **Alert acceptance / override rate** — per CDSS component (see below).
- Dashboard: `Product / Clinical Throughput`.

### 2.4 Revenue-cycle KPIs

- **Claim first-pass yield** — % claims accepted by the payer without correction on first submission. Target: ≥ 90% (Standard), ≥ 95% (Enterprise).
- **Days Sales Outstanding (DSO)** — median days from claim submission to remittance posting. Target: ≤ 45 days.
- **Denial rate (initial)** — % first-submission denials. Target: ≤ 8%.
- **Appeal success rate** — % appeals overturned in facility's favour. Target trend.
- **Net collection rate** — collections / net charges. Target: ≥ 95%.
- Dashboard: `Product / RCM`.

### 2.5 Patient engagement

- **Portal MAU** — monthly active patient portal users.
- **Message response time** — median first-response by clinical team.
- **Appointment self-service rate** — % appointments booked by patient without staff intervention.
- **NPS** — quarterly.
- Dashboard: `Product / Engagement`.

### 2.6 CDSS quality (post-market)

- **Alert acceptance rate** — per rule; target trend, not fixed.
- **Override reason mix** — distribution over time.
- **Time-to-first-action** — median minutes from alert to any action.
- **Fairness slices** — sensitivity by age band, sex, comorbidity where lawful.
- Dashboard: `Clinical / CDSS Monitoring`.

## 3. Executive views

Curated views for internal leadership and Customer QBRs:

| View | Audience | Cadence |
|---|---|---|
| Reliability summary | CTO, CISO, VP Support | Weekly |
| Adoption & activation | CEO, CPO, CSMs | Weekly |
| Clinical safety | Medical Director, CAB | Monthly |
| RCM performance | CFO, RCM leads | Monthly |
| Customer scorecard (per tenant) | CSM + Customer Exec | Monthly / QBR |

## 4. Data pipeline

- **Sources**: application events (Kafka), API gateway logs (S3), DB CDC, billing exports.
- **Warehouse**: dbt models under `ops/warehouse/` (to be built), partitioned by tenant and date.
- **PHI treatment**: warehouse is by default de-identified; PHI available only in tenant-scoped operational replicas with strict access.
- **Latency SLO**: see §1.5.

## 5. Access & privacy

- Grafana access via SSO with role-based folders.
- Per-tenant dashboards restricted to the tenant's own data and to CyMed staff with tenant scope.
- PHI never surfaces in cross-tenant aggregate views.
- Export from dashboards is logged.

## 6. Roadmap

Dashboards to be built next (in priority order):

1. `Reliability / API Availability` + `Latency` + `Error Rate` — pre-pilot must-have.
2. `Reliability / Job Health` — pre-pilot must-have.
3. `Reliability / Backup & DR` — pre-pilot must-have.
4. `Product / Clinical Throughput` — pilot week 1.
5. `Product / RCM` — pilot week 2.
6. `Clinical / CDSS Monitoring` — pilot week 4 (after Shadow-mode data accumulates).
7. `Product / Adoption` and `Engagement` — pilot week 4.
8. Executive summaries — pilot month 2.
