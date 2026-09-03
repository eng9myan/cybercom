# CyMed Pilot Agreement — Template

> **DRAFT — PENDING LEGAL REVIEW**
> Standalone paid pilot; may reference an MSA in place.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Commercial Lead — TBD>` |
| Review cadence | Quarterly |

---

**PILOT AGREEMENT**

This Pilot Agreement (the "Pilot") is entered into as of `<Effective Date>` between `<Provider Legal Entity — CyMed>` ("Provider") and `<Customer Legal Entity>` ("Customer"). Capitalised terms not defined here take the meaning in the MSA (if executed) or the Order Form.

## 1. Purpose

The Parties will conduct a paid, time-boxed pilot of the CyMed platform to evaluate its fitness for Customer's operational context and to establish measurable success criteria against which the Parties will decide whether to convert to a Standard or Enterprise subscription.

## 2. Pilot Term

- **Duration:** ninety (90) calendar days from the go-live date recorded in the Pilot kick-off memo.
- **Extension:** may be extended once, up to thirty (30) days, by written agreement.

## 3. Scope

| Item | Value |
|---|---|
| Edition(s) | `<Clinic / Hospital / Lab / Imaging / Pharmacy — select>` |
| Tier | Pilot |
| Site(s) | `<One site, address>` |
| Users | Up to `<N>` Authorised Users |
| Modules enabled | `<list>` |
| Integrations enabled | `<list — mark as sandbox / production>` |
| AI CDSS mode | Shadow (recommendations visible but not blocking) |

## 4. Fees

| Line | Amount | Currency | Notes |
|---|---:|---|---|
| Pilot subscription | `<amount>` | `<SAR / JOD / USD>` | Payable in advance, in two instalments (50 / 50). |
| Implementation (fixed) | `<amount>` |  | Includes environment provisioning, initial configuration, and one training cohort. |
| Data migration (per source, optional) | `<amount>` |  | Reconciliation report included. |

## 5. Success Criteria (Template)

The Parties agree the following measurable criteria. All figures are illustrative and must be finalised before go-live.

| # | Criterion | Metric | Target | Measured by | Frequency |
|---|---|---|---|---|---|
| 1 | Availability | Monthly Uptime % | ≥ 99.5% | Provider status report | Monthly |
| 2 | Adoption | % active licensed users / week | ≥ 80% | Product telemetry | Weekly |
| 3 | Task speed | Median encounter documentation time | −30% vs. baseline | Timed observation + telemetry | End of pilot |
| 4 | Order accuracy | CDSS-flagged interactions accepted | ≥ 60% | CDSS event log | Monthly |
| 5 | Claim first-pass yield (if RCM enabled) | % claims accepted at first submission | ≥ 90% | Payer ACK feed | Monthly |
| 6 | User satisfaction | Post-pilot NPS across all roles | ≥ 30 | Survey | End of pilot |
| 7 | Support responsiveness | SEV1 acknowledgement within target | 100% | Ticket data | End of pilot |

## 6. Conversion Credit

If Customer converts to a **Standard** or **Enterprise** subscription within thirty (30) days after the Pilot ends, Provider will credit **fifty percent (50%) of the Pilot subscription fees paid** against the first invoice of the new subscription.

If Customer does not convert, no credit applies; Customer may retain access to a read-only copy for thirty (30) days for data export.

## 7. Data Return and Deletion on Non-conversion

1. Provider will make Customer Data available for export in a documented open format (FHIR R4 for clinical data, DICOM for imaging, CSV for administrative data) for thirty (30) days from Pilot end.
2. After that period, Provider will delete Customer Data within a further thirty (30) days, subject to any Required-by-Law retention, and will issue a written certificate of deletion.

## 8. Clinical Governance during Pilot

1. Customer's medical director (or delegate) signs the CDSS enablement form (`docs/clinical/CLINICIAN_SIGNOFF_TEMPLATE.md`) before any CDSS output is displayed to users.
2. AI CDSS operates in **shadow mode** for the first four (4) weeks of the Pilot; graduation to advisory mode requires written Customer approval.
3. Customer retains sole responsibility for clinical decisions.

## 9. Confidentiality; Publicity

1. The MSA confidentiality terms apply.
2. Neither Party will issue press releases or public references without the other Party's prior written consent, not to be unreasonably withheld.

## 10. Warranty; Liability

1. Pilot Services are provided **on an evaluation basis**, "as is," except for the express security and data-protection obligations in the DPA / BAA.
2. Aggregate liability arising from the Pilot is capped at **fees paid** for the Pilot.

## 11. Termination

Either Party may terminate this Pilot on fifteen (15) days' written notice; Customer may terminate for cause on Provider's uncured material breach after five (5) business days. Unused pre-paid fees are refunded pro rata for terminations for cause by Customer.

## 12. Governing Law

As set out in the MSA. If no MSA is in place, the laws of `<Governing Law — placeholder>` apply.

---

## Signature Block

**Provider:** `<Provider Legal Entity — CyMed>`

Name: `______________________`
Title: `______________________`
Date: `______________________`
Signature: `______________________`

**Customer:** `<Customer Legal Entity>`

Name: `______________________`
Title: `______________________`
Date: `______________________`
Signature: `______________________`
