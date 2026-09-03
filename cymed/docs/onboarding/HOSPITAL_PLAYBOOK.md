# Hospital Onboarding Playbook

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Delivery — TBD>` |
| Review cadence | Quarterly |

---

## 0. Overview

This playbook governs multi-department hospital implementations of the CyMed Hospital edition (and any add-on Lab, Imaging, Pharmacy editions bought together). Each stage has explicit entry criteria, exit criteria, and RACI. The default timeline is **12 weeks** from kick-off to steady-state; larger deployments may be phased.

## 1. Stages

### Stage 1 — Discovery (Week 1)

**Entry:** signed MSA + Order Form; kick-off scheduled.
**Exit:** Discovery Report signed; scope frozen (v1); risk log opened.

**Activities**
- Stakeholder mapping (execs, clinical leaders, IT, finance, compliance).
- Departmental walkthroughs: ED, wards, OR, outpatient, pharmacy, lab, imaging, RCM.
- Legacy systems inventory + data volumes.
- Integration inventory (HIS, LIS, RIS, PACS, payer, national health exchanges, HR, GL).
- Regulatory in-scope list (CBAHI, SFDA MDR, CCHI, NPHIES, HIPAA/GDPR/PDPL).

### Stage 2 — Design (Weeks 2–3)

**Entry:** signed Discovery Report.
**Exit:** signed Design Book covering (a) target org model, (b) module configuration decisions, (c) integration architecture, (d) migration plan, (e) UAT plan, (f) training plan, (g) go-live method.

**Activities**
- Tenant + edition provisioning design.
- Master data model (facilities, departments, wards, beds, providers, cost centres).
- Order sets, formulary alignment, CDSS rule enablement decisions.
- Integration design (endpoints, message types, cadence, retry / error handling).
- Data migration blueprint (see `docs/onboarding/DATA_MIGRATION_PLAYBOOK.md`).

### Stage 3 — Data migration (Weeks 3–8)

**Entry:** signed Design Book; source system access confirmed.
**Exit:** two successful dry-runs against staging; reconciliation report accepted.

**Activities**
- ETL scripts developed under `D:/cybercom/cymed/tools/migration/`.
- Anchor entities first (facilities, departments, providers, patients, insurance).
- Longitudinal data second (encounters, orders, results, medications, documents).
- Imaging (DICOM) last, via SCP ingress or study-level import.
- Dry-runs against a staging tenant; reconcile counts, sums, timestamps, and sample records against source.

### Stage 4 — Configuration (Weeks 4–8, parallel with migration)

**Entry:** Design Book.
**Exit:** all modules configured to Design Book; configuration snapshot exported and versioned.

**Activities**
- Roles, permissions, and scope rules.
- Order sets, protocols, formulary, catalogues.
- Fee schedules, insurance plans, payer contracts.
- CDSS rule enablement, alert thresholds, override policy.
- Notifications (SMS, email, push).
- Report templates.

### Stage 5 — User Acceptance Testing (Weeks 8–10)

**Entry:** configuration complete; migration dry-run 2 passed; UAT plan approved.
**Exit:** UAT sign-off with zero SEV1 and zero SEV2 defects open; documented workarounds for SEV3 defects.

**Activities**
- Scenario execution by department leads (ED, OR, wards, outpatient, pharmacy, lab, imaging, RCM).
- End-to-end flows: registration → order → dispense/result → billing → claim.
- Integration end-to-end tests including error paths.
- Security testing: RBAC, break-glass, MFA reset, session revocation, audit-log completeness.

### Stage 6 — Go-live (Week 11)

**Entry:** UAT sign-off; go / no-go review passed; cut-over runbook rehearsed; command centre in place.
**Exit:** production live for all in-scope departments; cut-over report signed.

**Activities**
- Final incremental data sync (delta since last dry-run).
- DNS / integration cut-over per runbook.
- Command centre operational for 72 hours (Provider + Customer).
- Legacy system placed in read-only mode.
- Hourly status reviews for the first 24 hours.

### Stage 7 — Hypercare (Weeks 11–12, 2 weeks)

**Entry:** go-live complete.
**Exit:** hypercare exit review; issue log below thresholds (see below).

**Activities**
- On-site (or dedicated remote) senior engineer + clinical informaticist for two weeks.
- Daily stand-up with department leads.
- SEV1 target ≤ 1 open at any time; SEV2 target ≤ 3.
- Daily changelog to Customer's steering committee.
- Post-hypercare survey (adoption, satisfaction, gaps).

### Stage 8 — Steady-state

**Entry:** hypercare exit review signed.
**Exit:** ongoing.

**Activities**
- Standard support tiers (see `docs/support/SUPPORT_TIERS.md`).
- Quarterly business review with Customer Success Manager (Enterprise) or semi-annual (Standard).
- Change management for new modules, integrations, or rule updates.
- Annual DR test participation.

## 2. RACI

Roles: **R** = Responsible, **A** = Accountable, **C** = Consulted, **I** = Informed.

Abbreviations:
CyPM = CyMed Project Manager; CyTL = CyMed Tech Lead; CyClin = CyMed Clinical Informaticist; CySec = CyMed Security; CyCSM = CyMed CSM; CustPM = Customer PM; CustExec = Customer Executive Sponsor; CustClin = Customer Clinical Lead; CustIT = Customer IT; CustCompl = Customer Compliance; CustRCM = Customer RCM Lead; CustDept = Customer Department Head(s).

| Activity | CyPM | CyTL | CyClin | CySec | CyCSM | CustPM | CustExec | CustClin | CustIT | CustCompl | CustRCM | CustDept |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kick-off | A/R | C | C | C | C | R | A | C | C | C | C | I |
| Discovery workshops | R | C | R | C | I | A/R | I | R | R | R | R | R |
| Design Book | A | R | R | C | I | R | I | C | C | C | C | C |
| Data-migration ETL | C | A/R | I | C | I | R | I | I | R | I | C | I |
| Configuration | R | R | R | C | I | A | I | C | C | C | R | C |
| Integration build | C | A/R | I | C | I | R | I | I | R | I | I | I |
| UAT | R | C | R | I | I | A | I | R | R | I | R | R |
| Security review | C | R | I | A/R | I | R | I | I | R | R | I | I |
| CDSS enablement | C | I | A | I | I | R | A | R | I | R | I | I |
| Go / no-go decision | C | C | C | C | I | R | A | C | C | C | C | I |
| Cut-over | A/R | R | R | R | I | R | I | R | R | I | R | R |
| Hypercare | A/R | R | R | R | R | R | I | R | R | I | R | R |
| Steady-state | I | I | C | C | A/R | R | A | R | R | I | R | I |

## 3. 12-week Gantt (ASCII)

Columns are weeks (W1–W12). `#` = active, `>` = milestone.

```
Stage / Week                        | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 | W9 |W10 |W11 |W12 |
------------------------------------|----|----|----|----|----|----|----|----|----|----|----|----|
1. Discovery                        | ## |    |    |    |    |    |    |    |    |    |    |    |
   > Discovery Report signed        |  > |    |    |    |    |    |    |    |    |    |    |    |
2. Design                           |    | ## | ## |    |    |    |    |    |    |    |    |    |
   > Design Book signed             |    |    |  > |    |    |    |    |    |    |    |    |    |
3. Data migration                   |    |    | ## | ## | ## | ## | ## | ## |    |    |    |    |
   > Dry-run 1                      |    |    |    |    |    |  > |    |    |    |    |    |    |
   > Dry-run 2 + reconciliation     |    |    |    |    |    |    |    |  > |    |    |    |    |
4. Configuration                    |    |    |    | ## | ## | ## | ## | ## |    |    |    |    |
   > Config snapshot v1             |    |    |    |    |    |    |    |  > |    |    |    |    |
5. UAT                              |    |    |    |    |    |    |    | ## | ## | ## |    |    |
   > UAT sign-off                   |    |    |    |    |    |    |    |    |    |  > |    |    |
6. Go-live                          |    |    |    |    |    |    |    |    |    |    | ## |    |
   > Cut-over report signed         |    |    |    |    |    |    |    |    |    |    |  > |    |
7. Hypercare                        |    |    |    |    |    |    |    |    |    |    | ## | ## |
   > Hypercare exit review          |    |    |    |    |    |    |    |    |    |    |    |  > |
8. Steady-state (post W12)          |                                                          -> ongoing
Training (rolling)                  |    |    |    | ## | ## | ## | ## | ## | ## | ## |    |    |
Integrations (build → sandbox → prd)|    |    | ## | ## | ## | ## | ## | ## | ## | ## | ## |    |
Security review + pen test          |    |    |    |    |    |    | ## | ## | ## |    |    |    |
Executive steering committee        |    | ## |    | ## |    | ## |    | ## |    | ## |    | ## |
```

## 4. Entry / Exit gates (summary)

| Gate | Owner | Artifact |
|---|---|---|
| Kick-off complete | CyPM | Kick-off memo |
| Discovery complete | CustPM | Discovery Report v1.0 |
| Design complete | CyTL | Design Book v1.0 |
| Migration ready for prod | CyTL | Reconciliation Report — Dry-run 2 |
| Config complete | CyClin | Config Snapshot v1 (versioned) |
| UAT signed | CustPM | UAT Sign-off + defect log |
| Security signed | CySec | Security Review Report |
| Go / no-go | CustExec | Go / no-go minutes |
| Go-live | CyPM | Cut-over Report |
| Hypercare exit | CustPM | Hypercare Exit Review |

## 5. Escalation

- Delivery risk / schedule: CustPM → CyPM → CyCSM → CyMed VP Delivery.
- Clinical safety: CustClin → CyClin → CyMed Medical Director → CyMed CTO.
- Security incident: CustIT → CySec → CyMed CISO (per IR plan).
- Contractual: CustExec ↔ CyMed VP Sales / General Counsel.
