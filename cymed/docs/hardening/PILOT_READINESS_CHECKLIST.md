# Pilot Readiness Checklist — ALL-GREEN BEFORE PILOT

> Single page. Every row must be **GREEN** before pilot go-live. Any **AMBER** requires written waiver by the CTO. Any **RED** blocks go-live.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<VP Delivery — TBD>` |
| Review cadence | Per pilot |

Tenant: `<slug>` — Facility: `<name>` — Go-live target: `<YYYY-MM-DD>` — Reviewer: `<name>`

Legend: **G** = green (done, evidence linked) — **A** = amber (waiver on file) — **R** = red (blocker).

## Environments

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 1 | Production tenant provisioned in the correct region | ☐ | link |
| 2 | Staging tenant provisioned + kept in sync | ☐ | link |
| 3 | Configuration snapshot v1 exported and versioned | ☐ | link |
| 4 | Feature flags reviewed; only intended features on | ☐ | link |
| 5 | Rate limits and quotas per tenant set | ☐ | link |

## Migrations & data

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 6 | Dry-run 2 reconciliation report signed | ☐ | link |
| 7 | Delta ETL plan for cut-over rehearsed | ☐ | link |
| 8 | Rollback procedure rehearsed | ☐ | link |
| 9 | Legacy read-only plan agreed and dated | ☐ | link |

## Integrations (sandbox tests passing)

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 10 | NPHIES sandbox — eligibility / preauth / claims round-trip | ☐ | link |
| 11 | Each payer in scope — full test script suite (see `docs/regulatory/CCHI_APPLICATION_STATUS.md` §5) | ☐ | link |
| 12 | E-Rx routing — cross-pharmacy round-trip in sandbox | ☐ | link |
| 13 | Lab analyzer interfaces — HL7 / ASTM round-trip | ☐ | link |
| 14 | DICOM ingress — C-STORE + C-FIND from each configured modality | ☐ | link |
| 15 | Payment gateway — webhook signature + refund flow | ☐ | link |
| 16 | Identity provider (SSO) — round-trip with tenant IdP + MFA | ☐ | link |
| 17 | Notifications — SMS + email + push sample delivered | ☐ | link |
| 18 | External code sets refreshed (SNOMED / ICD / LOINC / RxNorm / national) | ☐ | link |

## Security

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 19 | Threat model reviewed for tenant scope (`docs/security/THREAT_MODEL.md`) | ☐ | link |
| 20 | External pen test findings — no open CRITICAL / HIGH | ☐ | link |
| 21 | Secrets rotated for the tenant; no shared or default creds | ☐ | link |
| 22 | MFA enforced for all privileged roles | ☐ | link |
| 23 | Break-glass procedure enabled + reviewers set | ☐ | link |
| 24 | Audit log sink verified end-to-end; export tested | ☐ | link |
| 25 | Data residency confirmed in-region for the tenant | ☐ | link |
| 26 | DPA / BAA signed and on file | ☐ | link |
| 27 | AUP + Terms link visible in product | ☐ | link |

## Reliability & backups

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 28 | Backup schedule verified; last restore verification within 30 days | ☐ | link |
| 29 | PITR window verified (RPO ≤ 15 min) | ☐ | link |
| 30 | Regional DR plan reviewed; last drill within 12 months | ☐ | link |
| 31 | Capacity plan headroom ≥ 2× expected pilot load | ☐ | link |
| 32 | Chaos scenarios (auth outage, payer outage, queue backlog) rehearsed | ☐ | link |

## Monitoring & alerting

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 33 | SLOs configured (see `docs/OPS_DASHBOARDS.md`) | ☐ | link |
| 34 | Alert routes tested (SEV1 pages the right people) | ☐ | link |
| 35 | Status page ready with the tenant's subsystems mapped | ☐ | link |
| 36 | Runbook links attached to each alert | ☐ | link |
| 37 | Dashboards for Reliability, Clinical, RCM, Adoption provisioned | ☐ | link |

## Training

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 38 | All roles trained to certification; register attached | ☐ | link |
| 39 | Quick-reference cards printed at each unit | ☐ | link |
| 40 | Preceptor coverage planned for first 2 weeks | ☐ | link |
| 41 | Downtime forms and paper kits distributed | ☐ | link |

## Clinical governance

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 42 | CDSS enablement form signed (`docs/clinical/CLINICIAN_SIGNOFF_TEMPLATE.md`) | ☐ | link |
| 43 | Escalation pathways published and posted | ☐ | link |
| 44 | Incident-report workflow tested end-to-end | ☐ | link |

## Contracts & compliance

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 45 | MSA + Pilot Agreement + Order Form fully executed | ☐ | link |
| 46 | Sub-processor list in DPA reviewed and up to date | ☐ | link |
| 47 | Payer / regulator sign-offs required for go-live obtained | ☐ | link |
| 48 | Insurance certificates on file (professional indemnity, cyber) | ☐ | link |

## Communications & escalation

| # | Item | Status | Evidence / owner |
|---:|---|:---:|---|
| 49 | War-room roster confirmed (24 h + 72 h shifts) | ☐ | link |
| 50 | Executive sponsor reachable within 5 min throughout cut-over | ☐ | link |
| 51 | Rollback trigger criteria acknowledged by CustExec + CyPM | ☐ | link |
| 52 | Post-cut-over reporting cadence agreed (T+24h, T+7d, T+30d, T+60d) | ☐ | link |

## Go / no-go

- CustExec sign-off: __________________________________ Date: ______________
- CyPM sign-off: ______________________________________ Date: ______________
- CyTL sign-off: ______________________________________ Date: ______________
- CISO sign-off: ______________________________________ Date: ______________
- Clinical Safety Officer sign-off: ___________________ Date: ______________
- Medical Director sign-off: __________________________ Date: ______________

**Decision:** ☐ GO   ☐ NO-GO   ☐ CONDITIONAL GO (conditions attached)
