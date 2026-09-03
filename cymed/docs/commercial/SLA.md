# CyMed Service Level Agreement (SLA)

> **DRAFT — PENDING LEGAL REVIEW**
> Incorporated by reference into the MSA as Exhibit A.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Reliability — TBD>` |
| Review cadence | Semi-annually, or on architecture change |

---

## 1. Scope

This SLA covers the availability of the CyMed production Services purchased under the MSA. It does not cover Pilot tier, sandbox / non-production environments, or one-time professional services.

## 2. Uptime Commitment

| Tier | Monthly Uptime Commitment |
|---|---:|
| Pilot | 99.5% (best effort — no credit) |
| Standard | **99.9%** |
| Enterprise | **99.95%** |

"Monthly Uptime Percentage" = ((Total Minutes in Month − Downtime Minutes) / Total Minutes in Month) × 100.

## 3. Definitions

- **"Downtime"** means any period, measured in one-minute intervals from Provider's external synthetic probes and internal SLO monitors, during which the CyMed API `GET /api/health` responds with HTTP 5xx, times out (> 30 s), or returns success for < 50% of probes across at least two geographic checkpoints for two consecutive minutes.
- **"Measurement window"** is the calendar month, `[first day 00:00:00 UTC, last day 23:59:59 UTC]`, aligned to the customer's tenant region.
- **"Recurring Fees"** means the recurring subscription fees for the affected edition and affected tenant in the month in which Downtime occurred.

## 4. Exclusions

Downtime does not include, and no credit is due for, unavailability caused by:

1. **Scheduled maintenance** announced ≥ 5 business days in advance, capped at 4 hours per calendar month, executed in the tenant's low-traffic window.
2. **Emergency maintenance** required to remediate a security incident, announced as soon as reasonably practical, capped at 60 minutes per calendar month.
3. **Force majeure** — events beyond Provider's reasonable control (war, insurrection, natural disasters, government action, regional cloud-provider region-wide outage lasting > 30 minutes, telecom carrier failures).
4. **Customer-caused** — misconfiguration of Customer's identity provider, network, VPN, firewall, DNS, or on-prem integration; misuse; capacity beyond licensed limits; use of unsupported client versions; breach of the AUP.
5. **Third-party services** not under Provider's control — NPHIES, payer connectivity, national e-Rx registries, DICOM sources upstream of the CyMed ingress, payment gateways, SMS gateways, and Customer-owned integrations.
6. **Beta / preview features** clearly labelled as such in the product.

## 5. Credit Schedule

If Provider fails to meet the applicable Monthly Uptime Commitment, Customer is entitled to a service credit computed against Recurring Fees for the affected edition and tenant in the month of the failure.

### 5.1 Standard tier (target 99.9%)

| Monthly Uptime | Service Credit |
|---|---:|
| < 99.9% and ≥ 99.0% | **10%** |
| < 99.0% and ≥ 95.0% | **25%** |
| < 95.0% | **50%** |

### 5.2 Enterprise tier (target 99.95%)

| Monthly Uptime | Service Credit |
|---|---:|
| < 99.95% and ≥ 99.5% | **10%** |
| < 99.5% and ≥ 99.0% | **25%** |
| < 99.0% | **50%** |

### 5.3 Cap

Total credits in any month are capped at 100% of Recurring Fees for that month.

## 6. Claim Procedure

1. Customer must submit a written claim within thirty (30) days after the end of the month in which the alleged Downtime occurred.
2. Claim must include tenant identifier, dates and times of the incident, and Customer's own logs where available.
3. Provider will respond within fifteen (15) business days with (a) validation and a credit or (b) a reasoned denial referencing measurement data.
4. Approved credits appear on the next monthly invoice. Credits are not refundable in cash; they may not be applied to fees for professional services, one-time fees, or third-party pass-through charges.
5. Credits are Customer's **sole and exclusive remedy** for Provider's failure to meet an availability commitment.

## 7. Incident Classification

Response and mitigation targets are commitments — they measure how quickly Provider acts, not how quickly a fix is deployed. Severity is set by Provider based on impact; Customer may propose reclassification.

| Severity | Definition | Target initial response | Target mitigation / workaround | Update cadence |
|---|---|---|---|---|
| **SEV1** | Service unavailable for the tenant; multiple critical workflows blocked; patient safety risk. | ≤ 15 min | ≤ 4 h | Every 30 min |
| **SEV2** | Major functional impairment affecting a significant subset of users or a critical workflow; no acceptable workaround. | ≤ 1 h (business hours), ≤ 2 h (24/7 for Enterprise) | ≤ 8 business hours | Every 2 h |
| **SEV3** | Moderate impairment; workaround exists; limited user impact. | ≤ 4 business hours | Next release train | Daily |
| **SEV4** | Minor issue, cosmetic defect, feature request, documentation question. | ≤ 1 business day | Backlog | On update |

## 8. Communication

- **Status page.** `https://status.cymed.example` reflects live status of subsystems (API, portal, DICOM ingress, RIS, LIS, RCM, integrations). RSS and webhook subscriptions are available.
- **Incident notifications.** SEV1 and SEV2 notifications are pushed to Customer's designated technical contacts within the response target above, via email and (for Enterprise) SMS + status webhook.
- **Post-incident review.** For every SEV1 and any SEV2 with mitigation > 8 h, Provider will deliver a written post-incident review within ten (10) business days, including root cause, timeline, corrective actions, and preventive actions.

## 9. Reporting

- Provider publishes a monthly availability report per tenant within ten (10) business days of month end.
- The report includes measured uptime, incident count by severity, mean time to acknowledge / mitigate, and any credits due.

## 10. Changes

Provider may amend this SLA on ninety (90) days' notice; any amendment that materially reduces Customer's rights during a Subscription Term does not take effect until renewal of that term.
