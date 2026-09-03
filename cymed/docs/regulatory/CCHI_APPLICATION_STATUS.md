# CCHI / Saudi Payer Application Status

> **DRAFT — PENDING LEGAL / COMMERCIAL REVIEW**
> Living document. Contains payer relationship data; treat as commercially confidential.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Payer Integrations — TBD>` |
| Review cadence | Monthly (payer status is volatile) |

---

## 0. Legend

| Status | Meaning |
|---|---|
| `NOT-STARTED` | Discovery only; no formal application. |
| `PROSPECTED` | Sales conversation opened; NDA if required. |
| `APPLIED` | Application / connectivity request submitted. |
| `SANDBOX` | Sandbox / UAT credentials issued; connector under development. |
| `TESTING` | Test scripts running; certification pending. |
| `CERTIFIED` | Payer / CCHI certification achieved. |
| `PRODUCTION` | Live for at least one tenant. |
| `BLOCKED` | Blocked by payer / regulator; blocker noted. |

## 1. Regulator / Aggregator

| Entity | Purpose | Status | Blocker / Next step | Owner |
|---|---|---|---|---|
| CCHI (Council of Cooperative Health Insurance) | Regulator, technical certification of health-insurance transactions | `<status>` | `<next step>` | `<owner>` |
| NPHIES (Saudi national platform) | Eligibility / preauth / claims / payment | `<status>` | `<next step>` | `<owner>` |
| SDAIA / PDPL | Data protection compliance for connectors | `<status>` | `<next step>` | `<owner>` |

## 2. Payer Status Matrix (KSA)

Populate per payer. Names below are indicative Saudi market payers — confirm current list before external distribution.

| # | Payer | Product line | Status | Connectivity | Certification stage | Blocker / Next step | Owner |
|---:|---|---|---|---|---|---|---|
| 1 | Bupa Arabia | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 2 | Tawuniya (The Company for Cooperative Insurance) | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 3 | MedGulf | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 4 | Al Rajhi Takaful (Health) | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 5 | AXA Cooperative | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 6 | Malath Cooperative Insurance | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 7 | Salama Cooperative Insurance | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 8 | Wataniya Insurance | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 9 | Gulf Union National Cooperative Insurance | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 10 | Buruj Cooperative Insurance | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 11 | Walaa Cooperative Insurance | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 12 | Amanah Insurance | Eligibility, Preauth, Claims | `<status>` | NPHIES | `<stage>` | `<step>` | `<owner>` |
| 13 | Saudi Re (reinsurance) | Reporting only | `<status>` | Reports | `<stage>` | `<step>` | `<owner>` |
| 14 | (add / revise per current market) | | | | | | |

## 3. Payer Contact List — Template

Store detailed contact records in the payer CRM. Minimum fields to keep in sync:

| Field | Notes |
|---|---|
| Payer legal name | |
| Product line (health / life / motor) | Health only in scope |
| Primary commercial contact | Name, role, email, phone |
| Technical (integration) contact | Name, role, email, phone |
| Escalation contact | Name, role, email, phone |
| Regulatory / compliance contact | Name, role, email, phone |
| Preferred communication channel | Email / portal / secure MFT |
| Data classification | Confidential |
| Renewal / review cadence | e.g., quarterly |

## 4. Connectivity Kit (per payer, standard)

Each payer onboarding requires:

- [ ] Signed technical integration agreement or NPHIES participation acknowledgement.
- [ ] Test environment credentials (per-tenant).
- [ ] Production credentials (per-tenant), gated by successful UAT.
- [ ] Certificate pinning: current cert + rollover cert.
- [ ] Rate limits & quotas negotiated and documented.
- [ ] Message specs: Eligibility (E250-equivalent), Preauth, Claims, Payment, Communication.
- [ ] Supported code sets (ICD-10-CM/AM, CPT/HCPCS/local, national drug codes, service codes).
- [ ] Error/reason code list.
- [ ] Escalation & SLA (payer side) documented.

## 5. Testing Script List (standard suite)

Every payer must pass this suite in sandbox before production cutover. Scripts live under `tools/payer-tests/` (private repo — commercial sensitivity).

| # | Script | Purpose | Pass criterion |
|---:|---|---|---|
| T-01 | Eligibility — active member | Valid response with coverage detail | Fields present per spec; latency < 3 s |
| T-02 | Eligibility — inactive member | Correct decline response | Response classified correctly |
| T-03 | Eligibility — dependent | Coverage inherited | Correct hierarchy |
| T-04 | Preauth — outpatient consult | Approval | Response code + reference retained |
| T-05 | Preauth — inpatient admission | Approval with LOS | Response fields captured |
| T-06 | Preauth — restricted drug | Denial with reason | Reason code mapped |
| T-07 | Preauth — appeal | Successful appeal cycle | State machine transitions correctly |
| T-08 | Claim — outpatient | Submission ACK | ACK retained; retry works after simulated fail |
| T-09 | Claim — inpatient (multi-item) | Submission ACK | Line-level detail preserved |
| T-10 | Claim — remittance reconciliation | Adjudication mapped to invoice | 100% lines reconciled |
| T-11 | Claim — resubmission on rejection | Correction cycle | New reference chain |
| T-12 | Claim — batch of 500 | Throughput | Within payer quota, no drops |
| T-13 | Communication — clinical attachment | Attachment uploaded | Ack + retention proof |
| T-14 | Payment — advice → posting | End-to-end | Accounting reconciles |
| T-15 | Error — invalid code | Descriptive error | Error code + human-readable message |
| T-16 | Error — expired token | Auto-refresh works | No dropped calls |
| T-17 | Failover — payer outage | Circuit breaker + queue | Auto-recovery on payer restore |
| T-18 | Data protection — minimum necessary | Field-level filters enforced | No PHI beyond spec |
| T-19 | Timezone / date boundary | Cross-midnight scenarios | Correct date attribution |
| T-20 | Currency handling | SAR only in scope | No rounding drift over batches |

## 6. Reporting

- Monthly payer scorecard: acceptance rate, average adjudication days, denial rate, appeal success.
- Quarterly business review with each payer's technical + commercial contact.
- Regulator liaison (CCHI, NPHIES) as required.

## 7. Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-08-19 | Initial draft matrix, testing suite, and connectivity kit. |
