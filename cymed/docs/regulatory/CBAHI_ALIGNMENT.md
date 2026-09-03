# CBAHI Alignment

> **DRAFT — PENDING LEGAL / REGULATORY REVIEW**
> CBAHI standards evolve; this document tracks how the CyMed platform supports each standard the platform can materially affect. It is not a substitute for a hospital's CBAHI compliance programme.

| Field | Value |
|---|---|
| Version | 0.1 (Draft) |
| Date | 2026-08-19 |
| Owner | `<Head of Regulatory Affairs / Clinical Safety Officer — TBD>` |
| Review cadence | Semi-annually or on CBAHI edition update |

---

## 0. Scope

Mapping of Central Board for Accreditation of Healthcare Institutions (CBAHI) standard areas that CyMed materially supports, to platform features and specific code paths. The mapping is intentionally conservative: where the standard is primarily process, we describe the platform's contribution (evidence, workflow, controls).

Paths are relative to `D:/cybercom/cymed/`.

## 1. Patient Identification (PI)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Two-identifier verification at every intervention | Barcode / QR scan + confirm on-screen; PPID (positive patient ID) service | `products/cymed/hospital/patient_id/` |
| Master Patient Index (MPI) with duplicate detection | Fuzzy matching on demographics + national ID; merge / unmerge workflow with audit | `products/cymed/patient/mpi/` |
| Newborn / unidentified patient handling | Temporary identifier + guided conversion at identity confirmation | `products/cymed/patient/temp_id.py` |
| Wristband issuance & re-print controls | Templates + audit of re-prints with reason | `products/cymed/hospital/wristbands/` |

## 2. Medication Safety (MMU)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| High-alert medications list & handling | Configurable list; alerts + dual-check requirement | `products/cymed/pharmacy/high_alert.py` |
| Drug–drug / drug–allergy interaction checking | Interaction engine at prescribe, dispense, administer | `products/cymed/pharmacy/interactions/`; `products/cymed/hospital/cpoe/` |
| Weight-based dosing & paediatric safety | Dose calculators bound to weight/age; hard stops beyond safe range | `products/cymed/hospital/dosing/` |
| Barcode-verified administration (BCMA) | 5-rights check with barcode; deviations logged with reason | `products/cymed/hospital/mar/` |
| Formulary alignment & non-formulary approval workflow | Formulary catalogues; substitution workflow | `products/cymed/pharmacy/formulary/` |
| Controlled substance ledger | Immutable ledger with reconciliation | `products/cymed/pharmacy/controlled_substances/` |
| Look-alike / sound-alike (LASA) alerts | LASA tags in formulary; user-facing prompt | `products/cymed/pharmacy/formulary/lasa.py` |

## 3. Incident Reporting (RM / QM)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Anonymous incident and near-miss reporting | In-app reporting from any screen with automatic context capture | `products/cymed/quality/incidents/` |
| Classification per HFMEA / severity matrix | Configurable taxonomy with organisational defaults | `products/cymed/quality/incidents/classify.py` |
| Root cause analysis (RCA) workflow | Structured RCA template with linked evidence and action plan | `products/cymed/quality/rca/` |
| Trending and dashboards | Incident trend dashboards by unit, severity, and category | `products/cymed/quality/dashboards/` |
| Regulatory reporting export | Templates for CBAHI, MoH, and internal boards | `products/cymed/quality/reports/` |

## 4. Infection Prevention & Control (IPC / IR)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Hand hygiene observation entry | Mobile-friendly capture; unit-level scoring | `products/cymed/ipc/hand_hygiene/` |
| HAI surveillance (CLABSI, CAUTI, SSI, VAP definitions) | Configurable definitions; case identification support from clinical data | `products/cymed/ipc/hai/` |
| Isolation orders + signage triggers | Isolation flag propagated to ADT + wristband + ward board | `products/cymed/hospital/adt/isolation.py` |
| Outbreak investigation | Line-list generator; contact tracing worksheet | `products/cymed/ipc/outbreak/` |
| Antimicrobial stewardship | Antimicrobial order sets; consult trigger; DDD tracking | `products/cymed/hospital/ams/` |

## 5. Nursing Care (NR)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Comprehensive nursing assessment on admission | Structured assessments with mandatory fields | `products/cymed/hospital/nursing/assessments/` |
| Fall risk (Morse) | Automated scoring + care plan trigger | `products/cymed/hospital/nursing/fall_risk.py` |
| Pressure ulcer risk (Braden) | Automated scoring + preventive orders | `products/cymed/hospital/nursing/braden.py` |
| Pain re-assessment cadence | Rules per pain score; nurse reminders | `products/cymed/hospital/nursing/pain.py` |
| Handoff (SBAR) | Structured SBAR at shift change | `products/cymed/hospital/nursing/sbar/` |

## 6. Anaesthesia & Sedation (AS)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Pre-anaesthesia assessment | Structured assessment; ASA class; risk flags | `products/cymed/hospital/anaesthesia/preop/` |
| Intra-op vitals capture | Anesthesia record integration | `products/cymed/hospital/anaesthesia/intraop/` |
| PACU discharge criteria | Aldrete score; discharge readiness | `products/cymed/hospital/anaesthesia/pacu/` |

## 7. Surgical Care (SC)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Surgical safety checklist (WHO) | Enforced at sign-in / time-out / sign-out | `products/cymed/hospital/or/safety_checklist.py` |
| Site marking documentation | Photo capture + provider confirmation | `products/cymed/hospital/or/site_marking.py` |
| Counts (instruments, sponges, sharps) | Structured counts with variance handling | `products/cymed/hospital/or/counts/` |
| Specimen labelling & chain of custody | Barcode + tenant-scoped LIS handoff | `products/cymed/hospital/or/specimens/` |

## 8. Emergency Department (ED)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Triage (CTAS / ESI) | Configurable triage protocol; time-to-provider tracking | `products/cymed/hospital/ed/triage.py` |
| Sepsis screening (qSOFA / SIRS) | CDSS alerts; sepsis bundle | `products/cymed/cdss/sepsis/` |
| Stroke / STEMI pathways | Time-critical checklists with door-to-needle / door-to-balloon timers | `products/cymed/hospital/ed/pathways/` |

## 9. Radiology / Imaging (RD)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Radiation dose recording | Per-study dose capture from modality metadata | `products/cymed/imaging/dose/` |
| Critical results notification | Read-back / acknowledgement workflow | `products/cymed/imaging/critical_results.py` |
| Reporting turnaround measurement | Report status timers + escalations | `products/cymed/imaging/report_tat.py` |

## 10. Laboratory (LB)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Critical results notification | Automated + call-back with acknowledgement | `products/cymed/laboratory/critical_results.py` |
| QC and calibration records | QC schedules + violation flags | `products/cymed/laboratory/qc/` |
| Blood bank crossmatch + traceability | ISBT 128 labelling; unit tracking | `products/cymed/laboratory/blood_bank/` |

## 11. Health Information Management (HIM)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Chart completeness & timely sign-off | Encounter closure timers; escalation to service chief | `products/cymed/hospital/documents/completeness.py` |
| Coding accuracy | Coder queue with query workflow; auto-suggestions | `products/cymed/rcm/coding/` |
| Retention & destruction rules | Per-record type retention aligned to KSA HIM rules | `products/cymed/him/retention/` |

## 12. Patient Rights (PR)

| Standard theme | CyMed feature | Code / config path |
|---|---|---|
| Informed consent capture (multi-language) | Templates in Arabic/English; signed digital consent with witness | `products/cymed/patient/consent/` |
| Advance directives | Structured storage with visibility on encounter header | `products/cymed/patient/advance_directives/` |
| Complaints management | Portal + staff workflow | `products/cymed/patient/complaints/` |

## 13. Governance & Leadership (GL)

Platform contribution:
- Board / committee dashboards from live operational data.
- Policy library with acknowledgement tracking.
- Credentialing / privileging register with expiry alerts.

Code paths: `products/cymed/governance/`; `products/cymed/hr/credentials/`.

---

## 14. Evidence generation for CBAHI surveys

- Every code path above emits standard **audit events** that can be exported per date range and unit.
- Report library includes "CBAHI evidence" bundles per standard area (`products/cymed/quality/reports/cbahi/`).
- Configuration snapshots are versioned so a facility can prove what rules were in force at a given time.

## 15. Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-08-19 | Initial draft. |
