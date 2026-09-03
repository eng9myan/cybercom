# SFDA Submission Pack — SaMD with CDSS (MDR Class B)

> **DRAFT — PENDING LEGAL REVIEW**
> Regulatory affairs must review and adapt to the current SFDA MDS-REQ / MDS-G issued by the Saudi Food and Drug Authority. Class determination requires local RA sign-off.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Regulatory Affairs — TBD>` |
| Review cadence | Per submission / renewal |

---

## 0. Scope

The CyMed clinical decision support (CDSS) module is a Software as a Medical Device (SaMD). Provisional class: **Class B** under SFDA Medical Device Regulation. This document lists the artefacts required for a technical file and the internal owners, and provides the skeletons for each. Nothing here substitutes for RA counsel or the latest SFDA guidance documents.

## 1. Master Checklist

Legend: **[ ]** open — **[~]** in progress — **[x]** complete.

### 1.1 Administrative

- [ ] Manufacturer identification + registration documents.
- [ ] Authorised Representative (AR) appointment (if applicable).
- [ ] Device family / model designation and unique device identifier (UDI) allocation.
- [ ] Cover letter and executive summary.

### 1.2 Device description

- [ ] Intended use / intended purpose statement.
- [ ] Indications for use; contraindications; warnings.
- [ ] Target patient population and clinical context (adult inpatient / outpatient; specific specialities).
- [ ] Description of software features covered (see §3).
- [ ] Version scope for this submission.

### 1.3 Classification

- [ ] Classification rationale (SaMD framework + national rules).
- [ ] Risk category (state of healthcare situation × significance of information; IMDRF SaMD framework).
- [ ] Applicable standards (see §1.9).

### 1.4 Quality Management System

- [ ] ISO 13485:2016 certification (or equivalent) — copy attached.
- [ ] Design & Development procedures (see §4).
- [ ] Change control procedure.
- [ ] CAPA procedure.
- [ ] Complaint handling procedure.
- [ ] Post-market surveillance procedure (see §7).
- [ ] Vigilance & FSCA procedures.

### 1.5 Risk management

- [ ] ISO 14971 Risk Management File (see §5).
- [ ] Risk management plan.
- [ ] Hazard analysis with clinical harm rating.
- [ ] Risk control measures and residual risk analysis.
- [ ] Benefit-risk determination.

### 1.6 Design and manufacture

- [ ] Software architecture description (matches `docs/architecture/`).
- [ ] Software of Unknown Provenance (SOUP) list with justification and version pinning.
- [ ] Verification and validation summary (see §6).
- [ ] Cybersecurity plan (aligns with IMDRF cybersecurity guidance; references `docs/security/`).
- [ ] Human factors / usability engineering report (IEC 62366-1).

### 1.7 Clinical

- [ ] Clinical Evaluation Report (see §8).
- [ ] Clinical validation plan and results (see `docs/clinical/CLINICAL_VALIDATION_PLAN.md`).
- [ ] Post-market clinical follow-up (PMCF) plan.

### 1.8 Labelling and information for users

- [ ] Instructions for use (IFU).
- [ ] User training materials (see `docs/onboarding/TRAINING_DECK_OUTLINE.md`).
- [ ] In-product labelling / disclaimers ("Advisory only; clinician has ultimate responsibility").
- [ ] Language: Arabic + English.

### 1.9 Applicable standards (working list)

- ISO 13485:2016 — QMS for medical devices.
- ISO 14971:2019 — Risk management.
- IEC 62304:2006/AMD1:2015 — Medical device software lifecycle.
- IEC 62366-1:2015 — Usability engineering.
- IEC 82304-1:2016 — Health software safety and security.
- IMDRF SaMD framework (Categorisation N10 / Application N12 / Clinical Evaluation N41).
- IMDRF Cybersecurity guidance.
- SFDA MDS-REQ 1 (Medical Device Marketing Authorisation Requirements) — current edition.
- SFDA MDS-G specific guidance — as applicable to the software category and cycle.

### 1.10 Submission

- [ ] Technical file compiled + indexed.
- [ ] Fees paid.
- [ ] Submitted via SFDA e-portal.
- [ ] Response plan for RFIs.

---

## 2. Technical File — Skeleton (index)

```
Technical File (v0.1) — CyMed CDSS
1. Cover letter
2. Table of contents
3. Administrative
   3.1 Manufacturer & AR
   3.2 UDI
4. Device description
   4.1 Intended use
   4.2 Indications & contraindications
   4.3 Features (per §3 below)
   4.4 Version scope
5. Classification
6. Applicable standards
7. QMS references (ISO 13485)
8. Design & Development
   8.1 SW architecture
   8.2 SOUP
   8.3 V&V summary
   8.4 Cybersecurity plan
   8.5 Human factors (IEC 62366)
9. Risk Management (ISO 14971)
   Ref: docs/regulatory/artifacts/rmf_v0.1.md
10. Clinical evaluation
    Ref: docs/regulatory/artifacts/cer_v0.1.md
11. Labelling & IFU
12. Post-market surveillance & PMCF
13. Vigilance
14. Declarations of conformity
Appendices
   A. Bill of materials & version manifest
   B. Test evidence (V&V protocols & reports)
   C. Clinical evidence
   D. Training completion records for internal QMS roles
```

---

## 3. Features in Scope (initial cut)

| # | Feature | Clinical intent | Non-clinical support |
|---:|---|---|---|
| 1 | qSOFA advisory | Early sepsis screening in adult inpatients | Trend view |
| 2 | NEWS2 advisory | Deterioration detection for adult inpatients | Escalation pathway |
| 3 | LACE index | Readmission risk at discharge | Discharge planning |
| 4 | Morse Fall Scale | Fall risk stratification | Fall prevention |
| 5 | Drug–drug / drug–allergy interactions | Prescribing safety | Formulary |
| 6 | AI triage (patient-facing) | Symptom-guided routing | Care navigation |

## 4. Design & Development — Procedure references

Internal SOPs (managed under the QMS) referenced by index. Path placeholders: `<QMS>/SOP-DEV-*` etc.

- `SOP-DEV-01` Software Development Lifecycle (IEC 62304).
- `SOP-DEV-02` Configuration Management.
- `SOP-DEV-03` Change Control.
- `SOP-DEV-04` Verification & Validation.
- `SOP-QMS-05` Design History File.
- `SOP-QMS-06` Traceability Matrix.

## 5. Risk Management File — Skeleton

```
RMF (v0.1) — CyMed CDSS
1. Scope & references
2. Risk management plan
3. Hazard identification (per feature per use case)
4. Risk estimation & evaluation
5. Risk control measures
6. Residual risk evaluation
7. Benefit-risk analysis
8. Post-production risk information plan
9. Traceability (Hazard → Requirement → Design → Test)
Appendix A. Hazard log (living)
Appendix B. FMEA — clinical
Appendix C. FMEA — cybersecurity
```

Illustrative hazard categories (non-exhaustive):
- Missed alert (false negative) on deteriorating patient.
- Alert fatigue leading to override of true positives.
- Wrong-patient advisory due to context switching.
- Delayed presentation due to system latency.
- Data corruption of vitals feed.
- Cybersecurity: unauthorised access modifying rule thresholds.

## 6. Verification & Validation

- Unit tests + integration tests + end-to-end tests, coverage targets per criticality class.
- Rule engine test suite: 100% branch coverage on published rule versions.
- Validation against reference cases signed off by the Clinical Advisory Board.
- Cybersecurity testing (SAST/DAST/SCA/pen test) — see `docs/security/PENTEST_PACK.md`.
- Usability testing per IEC 62366-1 with representative user groups; formative + summative.

## 7. Post-Market Surveillance (PMS) Plan — Skeleton

```
PMS Plan (v0.1) — CyMed CDSS
1. Objectives
2. Data sources
   2.1 Complaints
   2.2 Incidents / near-misses (in-product reporting)
   2.3 Field service reports
   2.4 Literature review
   2.5 Real-world telemetry (opt-in, de-identified where possible)
3. Metrics & thresholds
   3.1 Alert acceptance rate per rule
   3.2 Override reasons distribution
   3.3 Time-to-first-action after alert
   3.4 False-positive / false-negative estimates from adjudicated samples
4. Frequency of analysis: monthly + quarterly PSUR-equivalent
5. Trending & signal detection
6. Feedback into design (CAPA linkage)
7. PMCF plan (post-market clinical follow-up)
8. Reporting to authorities (vigilance thresholds)
```

## 8. Clinical Evaluation Report (CER) — Skeleton

```
CER (v0.1) — CyMed CDSS
1. Scope of the evaluation
2. Device description
3. Intended purpose and target population
4. State of the art (with literature search protocol)
5. Clinical data appraisal
   5.1 Data generated by CyMed (from `docs/clinical/CLINICAL_VALIDATION_PLAN.md`)
   5.2 Equivalence claims (if any) and justification
   5.3 Literature evidence
6. Analysis of clinical data
7. Conclusions on safety and performance
8. Benefit-risk consistent with RMF
9. Gaps → PMCF
10. References
Appendix A. Literature search log
Appendix B. Adjudication protocols
Appendix C. Statistical analysis plan
```

---

## 9. Ownership & Sign-off

| Section | Owner | Reviewer | Approver |
|---|---|---|---|
| QMS | Head of Quality | CTO | CEO |
| Risk Management File | Regulatory Affairs | Clinical Safety Officer | Medical Director |
| Cybersecurity | CISO | CTO | Medical Director |
| Clinical Evaluation | Medical Affairs | Clinical Advisory Board | Medical Director |
| Usability | Product | Clinical Safety Officer | CTO |
| PMS Plan | Regulatory Affairs | Medical Affairs | Medical Director |
