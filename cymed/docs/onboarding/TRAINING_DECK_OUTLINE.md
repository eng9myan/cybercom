# CyMed Training — Deck Outlines by Role

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Enablement — TBD>` |
| Review cadence | Per major release |

---

## 0. Common conventions

- Every course has: **duration**, **prerequisites**, **learning outcomes**, **hands-on labs**, **competency assessment**, **pass criterion**, **materials**.
- Delivery: instructor-led (in-person or virtual) + on-demand recordings + interactive labs on a dedicated training tenant seeded with realistic fixtures.
- Assessment: role-appropriate mix of scenario-based tests, task-based checkoffs, and, where relevant, precepted supervised production use.
- Certification: role certificate issued on pass; re-certification annually or on major release.
- Language: English + Arabic; localisation available for other markets.
- Materials: slide deck (PDF + editable), workbook, quick-reference card, and video walkthroughs.

---

## 1. Administrator (Tenant & Facility Admin)

- **Duration:** 8 hours (2 half-days) + 2-hour lab.
- **Prerequisites:** basic IT literacy; familiarity with the organisation's org structure and identity provider.
- **Learning outcomes:**
  1. Provision facilities, departments, wards, providers, and cost centres.
  2. Configure roles, permissions, and scope rules.
  3. Manage identity provider integration, MFA policy, session limits.
  4. Configure notifications, integrations, and API keys.
  5. Export audit logs; freeze accounts; run break-glass.
  6. Perform tenant backups and understand recovery scope.
- **Hands-on labs:**
  - L1: Create a facility, department, and 5 providers.
  - L2: Build a role with restricted PHI access; verify with a test user.
  - L3: Reset a user's MFA and revoke their sessions.
  - L4: Export the last 24 hours of audit logs to CSV; find a specific action.
  - L5: Add an OIDC IdP and test SSO round-trip.
- **Assessment:** timed scenario (60 min) covering all outcomes.
- **Pass criterion:** ≥ 85%.

---

## 2. Reception / Registration

- **Duration:** 4 hours + 2-hour supervised live shift.
- **Prerequisites:** none.
- **Learning outcomes:**
  1. Register new patients; resolve duplicates via MPI hints.
  2. Verify insurance eligibility (real-time + manual fallback).
  3. Schedule, reschedule, cancel appointments.
  4. Collect consents (visit consent, e-Rx, telehealth, data sharing).
  5. Handle walk-ins, no-shows, and priority patients.
  6. Perform check-in / check-out; take cash / card / insurance co-pay.
- **Hands-on labs:**
  - L1: Register a patient with an existing MPI match; merge duplicates.
  - L2: Book, reschedule, and cancel appointments across two providers.
  - L3: Handle a rejected eligibility response; capture manual reference number.
  - L4: Process a mixed-tender payment (part insurance, part cash).
- **Assessment:** end-to-end registration + check-in scenario (30 min) + supervised live shift signed off by supervisor.
- **Pass criterion:** ≥ 90% on scenario + supervised shift signed off.

---

## 3. Clinician (Physician / Dentist / Consultant)

- **Duration:** 6 hours + 8-hour precepted use over 2 clinical days.
- **Prerequisites:** clinical license; role assignment complete.
- **Learning outcomes:**
  1. Navigate patient chart efficiently (allergies, problems, meds, results).
  2. Write encounter notes and structured assessments; use templates.
  3. Place orders (labs, imaging, referrals, medications) using order sets.
  4. Interact with CDSS: interpret advisories, use override with reason.
  5. E-prescribe (routing to any CyMed pharmacy).
  6. Use the ambient scribe (if enabled) and validate the generated draft.
  7. Sign encounters; understand cosignature and delegation.
- **Hands-on labs:**
  - L1: Complete an outpatient encounter end-to-end.
  - L2: Order a lab panel + interpret results; sign off.
  - L3: E-prescribe two medications with a real interaction; respond to CDSS.
  - L4: Complete a discharge summary from an inpatient encounter.
  - L5 (if CDSS enabled): review a qSOFA / NEWS2 alert on a scenario patient.
- **Assessment:** case-based simulation graded by clinical informaticist + 2 precepted encounters.
- **Pass criterion:** simulation ≥ 85% + preceptor sign-off.

---

## 4. Nurse

- **Duration:** 6 hours + 8-hour precepted use per unit.
- **Prerequisites:** clinical license; role assignment complete.
- **Learning outcomes:**
  1. Perform intake, vitals, and structured assessments (pain, falls, pressure ulcer risk).
  2. Administer medications with the 5 rights + barcode / positive-patient-ID.
  3. Escalate deteriorating patients (NEWS2 pathway, rapid response call).
  4. Complete incident reports (see CBAHI alignment).
  5. Handoff (SBAR) and shift transfer.
- **Hands-on labs:**
  - L1: Full inpatient admission — intake, orders, MAR.
  - L2: Administer 4 scheduled meds using barcode ID; document one refusal.
  - L3: Complete a NEWS2 escalation on a deteriorating patient.
  - L4: File an incident report and follow-up.
- **Assessment:** simulation + preceptor sign-off.
- **Pass criterion:** ≥ 85% + preceptor sign-off.

---

## 5. Pharmacist

- **Duration:** 6 hours + 4-hour supervised dispense session.
- **Prerequisites:** licensed pharmacist; role assigned to pharmacy edition.
- **Learning outcomes:**
  1. Receive and validate prescriptions (paper + e-Rx).
  2. Run interaction / allergy / duplicate-therapy checks.
  3. Dispense, label, and counsel; handle refusals.
  4. Manage controlled substances ledger + audit.
  5. Process insurance adjudication + patient co-pay.
  6. Manage inventory (receiving, cycle count, expiry watch).
- **Hands-on labs:**
  - L1: Dispense an e-Rx with a flagged interaction; document counselling.
  - L2: Dispense a controlled substance with correct ledger entries.
  - L3: Resolve a rejected adjudication (formulary exception + prior auth).
  - L4: Perform a cycle count and reconcile variance.
- **Assessment:** live dispensing session graded by senior pharmacist.
- **Pass criterion:** ≥ 90% + supervisor sign-off; controlled substance workflow must be error-free.

---

## 6. Radiographer / Radiographic Technologist

- **Duration:** 5 hours + 4-hour precepted at modality.
- **Prerequisites:** licensed technologist; modality vendor training in place.
- **Learning outcomes:**
  1. Manage worklist (DICOM MWL) and patient identification.
  2. Perform image acquisition; ensure ID and study metadata are correct.
  3. QA images; flag repeats.
  4. Push studies to PACS-lite; verify report writer receives the study.
  5. Handle emergency / priority workflows.
- **Hands-on labs:**
  - L1: Pull a scheduled worklist entry; acquire images on a training modality (simulator); confirm archive.
  - L2: Repeat a bad image; document the reason.
  - L3: Handle a stat request; escalate to on-call radiologist.
- **Assessment:** modality-side observation.
- **Pass criterion:** preceptor sign-off; zero patient-ID mismatches.

---

## 7. RCM Staff (Coding / Billing / Claims)

- **Duration:** 8 hours (2 half-days) + 4-hour scenario clinic.
- **Prerequisites:** coding certification (or working towards); familiarity with local payer landscape (NPHIES / CCHI for KSA).
- **Learning outcomes:**
  1. Ensure encounter closure with all required documentation.
  2. Code diagnoses and procedures (ICD-10 / CPT / national code sets).
  3. Build a claim; validate against payer rules.
  4. Submit via NPHIES / payer connector; track ACK / adjudication.
  5. Manage denials — analyse, correct, appeal.
  6. Reconcile payments; post remittance; escalate DSO issues.
- **Hands-on labs:**
  - L1: Code and submit 5 encounters spanning outpatient, inpatient, day-care.
  - L2: Correct a denial for missing prior auth; resubmit and confirm ACK.
  - L3: Reconcile a payer remittance to claims; explain variance.
  - L4: Produce an aged-AR report and prioritise workqueue.
- **Assessment:** claims scenario (60 min).
- **Pass criterion:** ≥ 90% first-pass claim yield in the scenario; correct handling of the denial and remittance.

---

## 8. Materials master list

| Item | Format |
|---|---|
| Slide deck (per role) | PDF + editable source |
| Workbook | PDF |
| Quick-reference card | Two-sided PDF |
| Video walkthroughs | MP4 + captions (EN, AR) |
| Training tenant seed | Repeatable seed script under `tools/training/` |
| Assessment bank | Version-controlled JSON in `training/assessments/` |
| Certification template | Editable template |
