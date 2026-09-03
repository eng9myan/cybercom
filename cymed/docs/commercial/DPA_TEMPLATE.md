# Data Processing Agreement (DPA) — Template

> **DRAFT — PENDING LEGAL REVIEW**
> Aligned to Article 28 of Regulation (EU) 2016/679 (GDPR) and to equivalent processor obligations under the UK GDPR, KSA PDPL, and Jordanian PDPL. Local counsel must review for jurisdiction-specific additions (e.g., KSA National Data Governance rules).

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Data Protection Officer — TBD>` |
| Review cadence | Annually, or on regulatory change |

---

**DATA PROCESSING AGREEMENT**

This Data Processing Agreement (the "DPA") forms part of the Master Services Agreement (the "MSA") between:

- **`<Controller Legal Name>`** ("Controller"); and
- **`<Processor Legal Name — CyMed>`** ("Processor").

Capitalised terms not otherwise defined have the meaning in Article 4 of the GDPR.

## 1. Subject Matter, Duration, Nature and Purpose

1.1 **Subject matter.** Processing of Personal Data required for the provision of the CyMed platform and related services under the MSA.
1.2 **Duration.** The duration of the MSA and any post-termination export period.
1.3 **Nature and purpose.** Hosting, processing, and transmitting Personal Data — including special categories of data concerning health — to enable Controller's clinical, administrative, and revenue-cycle operations, and to enable secure access by Data Subjects to their own data.
1.4 **Types of Personal Data.** Identity, contact, demographic, insurance, clinical (diagnoses, medications, allergies, orders, results, notes), imaging (DICOM), consent records, telemetry, and audit metadata.
1.5 **Categories of Data Subjects.** Patients; Authorised Users (clinicians, administrative staff); guardians and next-of-kin; referrers.

## 2. Processor Obligations

2.1 Processor shall process Personal Data only on documented instructions from Controller, including with regard to transfers to a third country, unless required to do so by law; in that case Processor shall inform Controller before processing, unless the law prohibits such notice on important grounds of public interest.
2.2 Processor shall ensure that persons authorised to process the Personal Data have committed themselves to confidentiality or are under an appropriate statutory obligation of confidentiality.
2.3 Processor shall take all measures required pursuant to Article 32 of the GDPR — see **Annex II — Technical and Organisational Measures**.
2.4 Processor shall respect the conditions in Section 4 for engaging another processor.
2.5 Processor shall assist Controller by appropriate technical and organisational measures for the fulfilment of Controller's obligation to respond to requests from Data Subjects exercising their rights under Articles 15–22 of the GDPR.
2.6 Processor shall assist Controller in ensuring compliance with the obligations pursuant to Articles 32–36 (security, breach notification, data protection impact assessment, prior consultation).
2.7 At the choice of Controller, Processor shall delete or return all Personal Data after the end of the provision of Services relating to processing, and delete existing copies unless retention is Required by Law.
2.8 Processor shall make available to Controller all information necessary to demonstrate compliance with Article 28, and allow for and contribute to audits, including inspections, conducted by Controller or another auditor mandated by Controller.

## 3. Security Incidents and Personal Data Breaches

3.1 Processor shall notify Controller without undue delay, and in any event within seventy-two (72) hours, after becoming aware of a Personal Data Breach, providing the information required by Article 33(3) to the extent then known, with updates as more information becomes available.

## 4. Sub-processors

4.1 Controller grants Processor a general authorisation to engage sub-processors, subject to Processor's obligation to inform Controller of any intended change and to give Controller the opportunity to object on reasonable grounds within thirty (30) days.
4.2 Processor shall impose on each sub-processor, by written contract, data protection obligations no less protective than those set out in this DPA.
4.3 Processor remains fully liable to Controller for the performance of each sub-processor's obligations.
4.4 The current list of sub-processors is set out in **Annex III — Sub-processor Table**.

## 5. International Transfers

5.1 Where Personal Data originating in the EEA, the United Kingdom, or Switzerland is transferred to a country not covered by an adequacy decision, the Parties agree that such transfer is governed by the Standard Contractual Clauses adopted by the European Commission in Implementing Decision (EU) 2021/914 (the "SCCs"), which are hereby incorporated by reference:
- Module Two (Controller-to-Processor) applies where Processor is the data importer.
- Module Three (Processor-to-Processor) applies where a sub-processor is the data importer.
5.2 For UK transfers, the SCCs are supplemented by the UK International Data Transfer Addendum.
5.3 The specifics required by the SCCs (docking clause, optional clauses, competent supervisory authority, governing law) are completed in **Annex I** and **Annex II**.
5.4 For transfers involving KSA-originating data, Processor shall comply with the KSA Personal Data Protection Law and any transfer restrictions issued by SDAIA; Processor's default hosting region for KSA tenants is inside the Kingdom.

## 6. Data Subject Rights

6.1 Processor shall promptly notify Controller of any request from a Data Subject relating to Processor's processing and shall not itself respond except on documented instruction from Controller or where Required by Law.

## 7. Audits

7.1 Processor shall provide, on request and no more than once per year (except in the event of a Personal Data Breach or regulatory investigation), (a) its most recent SOC 2 Type II or ISO/IEC 27001 report and (b) written responses to a mutually agreed security questionnaire.
7.2 Additional audits may be conducted by Controller or a mutually agreed third-party auditor on thirty (30) days' notice, at Controller's expense, during Processor's normal business hours, subject to confidentiality obligations and without unreasonable disruption to Processor's operations.

## 8. Term and Termination

8.1 This DPA is effective for as long as Processor processes Personal Data on behalf of Controller under the MSA.

## 9. Miscellaneous

9.1 **Conflict.** In the event of a conflict between this DPA and the MSA regarding processing of Personal Data, this DPA controls. Where the SCCs apply, the SCCs prevail.
9.2 **Severability.** If any provision is held invalid, the remaining provisions remain in effect.

---

## Annex I — Description of the Processing

| Item | Description |
|---|---|
| Nature of processing | Hosting, storage, indexing, transmission, backup, DR, analytics on de-identified data |
| Purpose | Delivery of the CyMed platform in accordance with the MSA |
| Duration | For the term of the MSA + 90-day export period |
| Frequency | Continuous |
| Data types | Identity, contact, demographic, insurance, clinical, imaging (DICOM), consent, telemetry, audit metadata |
| Categories of Data Subjects | Patients, Authorised Users, guardians / next-of-kin, referrers |
| Recipients | Controller's Authorised Users; sub-processors listed in Annex III; competent authorities as Required by Law |
| Transfers to third countries | See Annex III |
| Retention | Per Controller instruction; default: for the term of MSA + statutory retention |

**SCC completion (Module Two, Controller-to-Processor):**

- Docking clause (Clause 7): applies.
- Sub-processor authorisation (Clause 9): general written authorisation (option (b)), with thirty (30) days' notice of changes.
- Redress (Clause 11): optional independent dispute resolution — not selected.
- Liability (Clause 12): as per SCCs.
- Governing law (Clause 17): `<Member State — e.g., Ireland>`.
- Competent supervisory authority (Clause 18): `<Supervisory Authority>`.
- Jurisdiction (Clause 18): courts of `<Member State>`.

## Annex II — Technical and Organisational Measures

Processor implements the following measures. Detail is maintained in the security programme documents; summary here.

| Domain | Measure |
|---|---|
| Access control | SSO, SAML/OIDC, MFA enforced for privileged access; least-privilege RBAC; quarterly access reviews |
| Encryption in transit | TLS 1.2+; internal service-to-service mTLS |
| Encryption at rest | AES-256; envelope encryption with regional KMS; per-tenant keys for hospital / lab / imaging editions |
| Key management | HSM-backed KMS; key rotation ≥ annually; separation of duties for key custodians |
| Network security | Private VPC; WAF; DDoS protection; segmented subnets per environment; deny-by-default egress |
| Application security | SDLC with peer review, SAST, SCA, secret scanning, dependency updates; annual third-party penetration test |
| Vulnerability management | Continuous scanning; SLA per severity (Critical 7 d, High 30 d, Med 90 d) |
| Logging and monitoring | Centralised, tamper-evident audit logs; retention 12 months hot / 7 years cold; SIEM alerting |
| Backup and DR | Encrypted daily backups; PITR; RPO ≤ 15 min, RTO ≤ 4 h (Enterprise); tested annually |
| Personnel | Background checks per local law; annual security + privacy training; NDAs |
| Vendor management | Sub-processor security review + BAA / DPA before onboarding |
| Physical security | Data centres with SOC 2 or ISO 27001; biometric access; 24/7 monitoring |
| Incident response | 24/7 on-call; documented IR plan; annual tabletop |
| Business continuity | Tested annually; multi-AZ deployment; region-level DR for Enterprise |
| Pseudonymisation | Available on request; standard for analytics data |

## Annex III — Sub-processor Table (Template)

Populate before contract signature. Fields marked `<...>` are per-tenant.

| # | Sub-processor legal name | Service provided | Location(s) of processing | Data categories processed | Safeguard for transfers | Onboarded date |
|---:|---|---|---|---|---|---|
| 1 | `<Cloud provider>` (e.g., AWS / Azure / GCP / Oracle Cloud) | IaaS, managed data services | `<Region — e.g., me-central-1 (UAE)>` | All | Regional hosting; SCCs where transferred out of EEA | `<YYYY-MM-DD>` |
| 2 | `<CDN / WAF provider>` | Edge, WAF, DDoS | Global edge, metadata only | Telemetry, non-PHI metadata | SCCs; DPF (if US) | `<YYYY-MM-DD>` |
| 3 | `<Email delivery>` | Transactional email | `<Region>` | Contact metadata | SCCs; DPF | `<YYYY-MM-DD>` |
| 4 | `<Observability / logs>` | Metrics, logs, traces | `<Region>` | Telemetry, hashed identifiers | SCCs | `<YYYY-MM-DD>` |
| 5 | `<Payment gateway>` | Card acquiring | Regional | PAN handled by processor via tokenisation | PCI DSS Level 1; SCCs | `<YYYY-MM-DD>` |
| 6 | `<NPHIES / payer bridge>` | KSA payer connectivity | KSA | Insurance, clinical minimum necessary | Domestic processing | `<YYYY-MM-DD>` |
| 7 | `<AI / model provider — optional>` | Model inference for scoped features | `<Region>`, no training on Customer Data | Text and structured inputs per feature | Opt-in per tenant; SCCs | `<YYYY-MM-DD>` |

---

## Signature Block

**Controller:** `<Controller Legal Name>`

Name: `______________________`
Title: `______________________`
Date: `______________________`
Signature: `______________________`

**Processor:** `<Processor Legal Name — CyMed>`

Name: `______________________`
Title: `______________________`
Date: `______________________`
Signature: `______________________`
