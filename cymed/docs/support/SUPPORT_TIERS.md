# CyMed Support Tiers

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Support — TBD>` |
| Review cadence | Semi-annually |

---

## 1. Severity Definitions

| Severity | Definition | Examples |
|---|---|---|
| **SEV1** | Production down for the tenant, OR a critical clinical / safety issue with no acceptable workaround. Data loss or PHI exposure risk. | API 5xx > 5% sustained; auth broken; CDSS silently suppressing alerts; DICOM ingress halted with backlog growing; suspected PHI leak. |
| **SEV2** | Major function impaired; significant subset of users or a critical workflow affected; a workaround exists but is not acceptable long-term. | E-Rx failing for one payer; slow lab results interface; report generation broken. |
| **SEV3** | Moderate issue; workaround exists; limited user impact. | Cosmetic UI defect on one screen; a rarely-used report shows wrong footer; non-critical integration retrying. |
| **SEV4** | Minor issue, question, or feature request. | How-to question; enhancement request; documentation gap. |

Provider assigns severity based on impact. Customer may propose re-classification; disputes escalate per §6.

## 2. Response and Resolution Targets

Response = human acknowledgement + initial triage. Resolution / workaround = a working path is available or the incident is closed.

### 2.1 Standard tier (business hours + SEV1 on-call)

| Severity | Initial response | Workaround target | Update cadence |
|---|---:|---:|---|
| SEV1 | ≤ 30 min (24/7 hotline) | ≤ 4 h | Every 30 min |
| SEV2 | ≤ 2 business hours | ≤ 8 business hours | Every 2 h |
| SEV3 | ≤ 1 business day | Next release train | On update |
| SEV4 | ≤ 2 business days | Backlog | On update |

### 2.2 Enterprise tier (24/7 for SEV1–SEV2)

| Severity | Initial response | Workaround target | Update cadence |
|---|---:|---:|---|
| SEV1 | ≤ 15 min (24/7) | ≤ 4 h | Every 30 min |
| SEV2 | ≤ 1 h (24/7) | ≤ 8 h | Every 2 h |
| SEV3 | ≤ 4 business hours | Next release train | Daily |
| SEV4 | ≤ 1 business day | Backlog | On update |

## 3. Business Hours

- Definition: Sunday–Thursday 08:00–18:00 local tenant timezone (Gulf); Monday–Friday 09:00–18:00 elsewhere. Public holidays observed per tenant calendar.
- **24/7** = 24 hours a day, 7 days a week, including public holidays.

## 4. Channels

| Channel | Availability |
|---|---|
| Support portal (ticket) | 24/7 (SLAs apply per §2) |
| Email | 24/7 (creates a ticket) |
| Phone (SEV1 hotline) | 24/7 for both tiers, SEV1 only for Standard |
| Chat (in-app) | Business hours (Standard); 24/7 (Enterprise) |
| Status page | 24/7 |
| CSM (Enterprise) | Business hours + on-call escalation |
| Named clinical informaticist (Enterprise, hypercare & first 90 days post-go-live) | Business hours |

Requests via unofficial channels (personal messaging, direct email to individuals) do not start the SLA clock.

## 5. Escalation Path

1. **L1 Support** — receives, triages, applies known-good remediation.
2. **L2 Support** — investigates, applies configuration/data fixes, coordinates with product/engineering.
3. **L3 Engineering** — code-level investigation and fix.
4. **Incident Commander** — assigned for every SEV1 and any SEV2 exceeding target; owns comms.
5. **Head of Support** — for SEV1 breaches of target and for cross-team blockers.
6. **Executive escalation** — VP Support / CTO / CEO, in that order, per the customer escalation matrix.

Customer escalation matrix (template)

| Level | CyMed contact | Customer contact |
|---|---|---|
| Day-to-day | Assigned engineer | Customer Ops lead |
| L2 | Support Manager | Customer PM |
| L3 | Head of Support | CIO / CMIO |
| Exec | VP Support | Executive Sponsor |

## 6. Reclassification & Disputes

- Customer may request severity reclassification at any time; CyMed responds within 30 min for SEV1/SEV2, 4 business hours otherwise.
- Unresolved disputes escalate to Head of Support within 1 business day.

## 7. Reporting

- Monthly per-tenant support report: ticket volume, SLA attainment by severity, top root causes, list of open issues > 14 days.
- Quarterly business review (Enterprise): trend analysis + roadmap alignment.

## 8. Exclusions

Support does not cover:
- Customer-owned integrations or customisations.
- Third-party services outside CyMed's control (NPHIES, payer, DICOM sources, SMS gateway).
- Training-on-demand outside the entitled cohorts (professional services rates apply).
- Data recovery from user error not covered by standard backup RPO/RTO (billable as professional services if feasible).

## 9. After-hours SEV1 hotline

- Number per region published in the support portal.
- Staffed by an on-call engineer with SLA-bound response times.
- Recording announces the SLA and the ticket number generated for the call.

## 10. Language & regional cover

- Primary: English, Arabic.
- Follow-the-sun coverage between regional hubs to meet 24/7 targets.
