# Clinician Sign-off — CDSS Enablement (Local Medical Director)

> **DRAFT — PENDING LEGAL / CLINICAL REVIEW**
> Required before any CyMed CDSS component graduates from Shadow mode to Advisory mode at a tenant.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Clinical Affairs — TBD>` |
| Review cadence | Per tenant; re-signed at each material rule change |

---

## 1. Tenant & Facility Details

| Field | Value |
|---|---|
| Tenant legal name | `______________________________________` |
| Tenant slug | `______________________` |
| Facility / site(s) covered by this sign-off | `______________________________________` |
| Environment | `[ ] Production   [ ] Staging` |
| Effective date | `YYYY-MM-DD` |

## 2. CDSS Components Enabled

Check each component enabled by this sign-off; specify the version.

| Component | Enable? | Version | Mode | Threshold overrides (if any) |
|---|:---:|---|---|---|
| qSOFA | [ ] | v___ | [ ] Shadow  [ ] Advisory  [ ] Blocking | ______________ |
| NEWS2 | [ ] | v___ | [ ] Shadow  [ ] Advisory  [ ] Blocking | ______________ |
| LACE | [ ] | v___ | [ ] Shadow  [ ] Advisory  [ ] Blocking | ______________ |
| Morse Fall Scale | [ ] | v___ | [ ] Shadow  [ ] Advisory  [ ] Blocking | ______________ |
| Drug interactions | [ ] | v___ | [ ] Shadow  [ ] Advisory  [ ] Blocking | ______________ |
| AI Triage (patient-facing) | [ ] | v___ | [ ] Shadow  [ ] Advisory  [ ] Blocking | ______________ |

**Notes on modes**
- **Shadow** — outputs are logged; not shown to users.
- **Advisory** — outputs shown to users; user retains full clinical judgement. Recommended default.
- **Blocking** — outputs require user action (e.g., double-check) before proceeding. Enable only where safety benefit is documented and clinical governance approves.

## 3. Attestations by the Medical Director

By signing, the undersigned confirms, in respect of the components enabled above:

1. I have reviewed the intended use, indications, contraindications, and warnings for each enabled component, as set out in the current Instructions for Use.
2. I have reviewed the validation evidence provided by CyMed (`docs/clinical/CLINICAL_VALIDATION_PLAN.md`, current reports).
3. I have assessed the fit of each component to our patient population and workflows.
4. I confirm the workflows, escalation pathways, and staffing to safely respond to the outputs are in place at the facilities named above.
5. I confirm the training completion of the relevant staff before go-live in the enabled mode.
6. I acknowledge that CyMed CDSS is a **decision-support** tool: clinical decisions remain the responsibility of the treating clinician and this facility's governance.
7. I acknowledge that CyMed will operate the components in Shadow mode for a minimum of 4 weeks before transitioning to Advisory mode, unless a specific waiver is documented below.
8. I authorise the collection of de-identified performance metrics for post-market clinical follow-up, as per the DPA in place.

## 4. Site-specific Configuration

| Item | Value / Notes |
|---|---|
| Alert delivery channels enabled | `[ ] In-app banner  [ ] MAR  [ ] Ward board  [ ] SMS to on-call  [ ] Rapid response call` |
| Escalation pathway (e.g., NEWS2 ≥ 7) | `______________________________________` |
| Override policy (require reason) | `[ ] Yes    [ ] No` |
| High-alert medication list custom to facility | `[ ] Uses CyMed default   [ ] Overrides — attached` |
| Formulary alignment reviewed | `[ ] Yes    [ ] N/A` |
| Language(s) enabled | `______________________________________` |

## 5. Governance & Post-market Review

| Item | Value |
|---|---|
| Named Clinical Safety Officer at facility | `______________________` |
| Frequency of local governance review of alerts / overrides | `[ ] Weekly  [ ] Monthly  [ ] Quarterly` |
| Committee name receiving reports | `______________________` |
| Serious-incident escalation contact (24/7) | `______________________` |
| Waivers / exceptions (attach) | `______________________________________` |

## 6. Sign-off

**Medical Director (or equivalent)**

Name: `______________________________________`
Title: `______________________________________`
Licence #: `______________________________________`
Date: `______________________________________`
Signature: `______________________________________`

**Clinical Safety Officer**

Name: `______________________________________`
Title: `______________________________________`
Date: `______________________________________`
Signature: `______________________________________`

**Chief Executive / Administrative Sponsor**

Name: `______________________________________`
Title: `______________________________________`
Date: `______________________________________`
Signature: `______________________________________`

**CyMed — Countersignature**

Name: `______________________________________`
Title: `Clinical Informaticist / Medical Affairs`
Date: `______________________________________`
Signature: `______________________________________`

---

## Appendix A — Change of enabled components

Any change to §2 or §4 requires a new page appended below with the delta, effective date, and re-signature by the Medical Director and Clinical Safety Officer.

| Date | Change | MD signature | CSO signature |
|---|---|---|---|
| | | | |
| | | | |
