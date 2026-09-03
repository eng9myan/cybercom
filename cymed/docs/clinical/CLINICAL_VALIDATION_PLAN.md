# Clinical Validation Plan — CDSS, Interactions Engine, AI Triage

> **DRAFT — PENDING CLINICAL & REGULATORY REVIEW**
> Feeds the Clinical Evaluation Report (CER) in the SFDA submission pack and the risk management file.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Medical Director / Head of Clinical Affairs — TBD>` |
| Review cadence | Per released rule pack; at minimum semi-annually |

---

## 0. Purpose

Establish a three-arm validation strategy that yields defensible evidence for (1) rule-based CDSS (qSOFA, NEWS2, LACE, Morse), (2) the drug interactions engine, and (3) the AI triage feature. Evidence supports regulatory submission (SFDA MDR Class B), tenant on-boarding sign-off, and post-market surveillance.

## 1. Devices under evaluation

| # | Component | Intended use | Population | Regulatory scope |
|---:|---|---|---|---|
| 1 | qSOFA advisory | Bedside screening for sepsis (SIRS-agnostic quick score) | Adult inpatients (≥ 18 y) outside ICU | SaMD in scope |
| 2 | NEWS2 advisory | Early warning of clinical deterioration | Adult non-pregnant patients on general wards | SaMD in scope |
| 3 | LACE index | Post-discharge readmission risk | Adult inpatients being discharged | SaMD in scope |
| 4 | Morse Fall Scale | Fall risk stratification | Adult inpatients | SaMD in scope |
| 5 | Drug interactions engine | Prescribing safety at CPOE + dispense + BCMA | All ages, formulary-agnostic | SaMD in scope |
| 6 | AI triage (symptom-guided routing) | Non-diagnostic navigational advisory to patients / receptionists | Adults; caregivers for children (with adult inputting) | SaMD in scope, non-diagnostic advisory |

## 2. Endpoints

### 2.1 Primary endpoints

| Component | Primary endpoint | Definition | Reference standard |
|---|---|---|---|
| qSOFA | **Sensitivity** ≥ 0.80 for sepsis / septic shock within 24 h of trigger | Sepsis-3 adjudication by 2 independent intensivists (blinded) | Sepsis-3 (Singer 2016) definition |
| NEWS2 | **Sensitivity** ≥ 0.85 for a composite outcome (unplanned ICU transfer, rapid response call, or death) within 24 h | Chart adjudication | Composite outcome per RCP NEWS2 |
| LACE | **AUC** ≥ 0.70 for unplanned 30-day readmission or death | Longitudinal follow-up | Registry linkage |
| Morse | **AUC** ≥ 0.70 for inpatient fall within stay | Adjudicated incident report | Facility incident data |
| Interactions engine | **Sensitivity** ≥ 0.95 for a benchmark list of major interactions (curated by clinical pharmacy) | Reference drug knowledgebase + expert set | Curated reference set (v1.0) |
| AI triage | **Safe-triage rate** ≥ 0.95 (proportion of cases where the recommended acuity ≥ reference acuity) | Adjudicated by physician panel | Reference acuity per adjudication protocol |

### 2.2 Secondary endpoints

Reported for all components:

- **Specificity**, **PPV**, **NPV**.
- **AUC** (or PR-AUC where prevalence is low).
- **Calibration** (Hosmer–Lemeshow or Brier as applicable).
- **Time to alert / recommendation** (median, p95).
- **Alert acceptance rate**; **override reasons** distribution (prospective only).
- **Missed alert rate** (adjudicated false negatives; retrospective + prospective).
- **Alert burden** (alerts per 100 patient-hours).
- **Fairness slices**: age band, sex, comorbidity burden, primary language, insurance status (where lawful to collect).

## 3. Three-arm design

### Arm A — Rule cases (synthetic)

- Curated deterministic case library per component; expected outputs pre-labelled.
- Passes 100% of rule cases before any real-data validation.
- Regression-gated in CI; blocks release on failure.

Deliverables:
- Case library under `products/cymed/cdss/tests/rule_cases/`.
- Coverage report per rule with branch coverage ≥ 95%.

### Arm B — Retrospective real data

- Historical de-identified records from partner sites.
- Chart adjudication protocol pre-specified.
- Blinded scoring; adjudicators do not see CyMed output during adjudication.
- Sample size per §4.

Deliverables:
- Data-use agreement per partner (see DPA sub-processor guidance where applicable).
- Retrospective analysis report per component.
- Locked SAP (§5) before analysis.

### Arm C — Prospective (pilot / real-world)

- Enabled only for tenants that have signed the CDSS enablement form (`docs/clinical/CLINICIAN_SIGNOFF_TEMPLATE.md`).
- Runs first in **shadow mode** (outputs recorded, not shown) for 4 weeks; then advisory mode.
- Adjudication of a random sample of positives and negatives (per §4).
- Registered as post-market clinical follow-up (PMCF) evidence.

Deliverables:
- PMCF protocol amendment per tenant.
- Monthly monitoring reports; quarterly analysis reports.
- Signal detection with pre-specified alerting thresholds.

## 4. Sample-size calculations (illustrative)

Assumptions and formulae below drive the target sample per arm. Final numbers are locked in the SAP before analysis.

### 4.1 Sensitivity target (dichotomous outcome)

Target = p (sensitivity or safe-triage rate). Width w of the two-sided 95% CI half-width uses the Wilson interval, with normal approximation for planning:

`n_positives ≈ (1.96^2 × p × (1 − p)) / w^2`

Planning values (retrospective arm):

| Component | Target p | Half-width w | Positives required | Notes |
|---|---:|---:|---:|---|
| qSOFA (sepsis) | 0.80 | 0.05 | ≈ 246 | Total N depends on sepsis prevalence; target ≥ 1,500 |
| NEWS2 (composite deterioration) | 0.85 | 0.05 | ≈ 196 | Assume prevalence ≈ 8% → target ≥ 2,500 |
| Interactions engine | 0.95 | 0.03 | ≈ 203 | Curated benchmark set — draw 250 |
| AI triage (safe-triage rate) | 0.95 | 0.03 | ≈ 203 | Retrospective + simulated cases |

### 4.2 AUC target

Test H0: AUC = 0.5 vs. H1: AUC ≥ 0.70 with α = 0.05 (two-sided) and power = 0.80. Under Hanley–McNeil approximation, needed positives ≈ 60 (with matched controls), so N total ≈ 60 × (1 + 1/prev).

Planning values:

| Component | Target AUC | Positives required | Total N (est.) |
|---|---:|---:|---:|
| LACE (30-d readmission or death) | 0.70 | ≥ 100 events | ≥ 1,000 |
| Morse (falls) | 0.70 | ≥ 100 events | ≥ 3,300 (prev ≈ 3%) |

### 4.3 Prospective arm

For each component:
- Shadow-mode observation window: 4 weeks.
- Adjudication random sample: 100 positives + 100 negatives, or all if fewer, per month.
- Duration until pre-specified evidence is reached, minimum 12 weeks.

## 5. Statistical Analysis Plan (SAP)

- SAPs are pre-registered and locked (git-tagged) before any comparison.
- Point estimates with 95% CIs (Wilson for proportions; DeLong for AUC differences).
- Missing data handling declared per component (default: complete-case for primary; sensitivity analysis with multiple imputation).
- Multiple comparisons across secondary endpoints controlled by Benjamini–Hochberg at 5% FDR.
- Subgroup analyses pre-specified for age, sex, comorbidity, primary language (fairness slices).
- Interim analyses defined only for prospective arm with alpha spending function.

## 6. Governance

- **Clinical Advisory Board (CAB)** reviews protocols and reports; independent Chair.
- **Adjudicators** are external clinicians blinded to CyMed output.
- **Data governance**: retrospective de-identified data under a DPA; prospective per patient-level consent where required by law and IRB approval where applicable.
- **Change control**: any change to a rule pack in production requires re-run of Arm A regression; if the change materially affects performance, re-analysis of Arms B and/or C.

## 7. Reporting

- Public-facing methods note for each component after Arm B.
- Internal Clinical Evaluation Report updates (CER) at each major release.
- Peer-reviewed publication considered for landmark analyses (LACE registry linkage; NEWS2 real-world impact).

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Adjudicator variability | Two adjudicators + adjudication rules + Cohen κ reporting |
| Site heterogeneity | Multi-site sample; mixed-effects models; sensitivity by site |
| Data quality gaps | Pre-registered inclusion criteria; sensitivity analysis |
| Publication bias in reference standards | Multiple reference sources; conservative primary endpoint |
| Fairness gaps | Slice metrics; escalation trigger for material disparities |

## 9. Deliverables & tracking

Artefacts stored under `docs/clinical/artifacts/` (created per component + version):

- `RULE_CASES_<component>_<version>.md`
- `RETRO_REPORT_<component>_<version>.md`
- `PROSPECTIVE_MONITORING_<component>_<yyyymm>.md`
- `SAP_<component>_<version>.md` (git-tagged)
- Adjudication protocols and completed forms.
