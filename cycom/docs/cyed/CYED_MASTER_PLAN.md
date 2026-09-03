# CyED — School Management System · Master Plan

**Status:** Planning (no code yet)
**Date:** 2026-08-05
**Owner:** Cybercom
**Thesis:** CyED is a specialized, AU-first school-management system built on the **CyCom platform** — reusing its multi-tenant Django core, ERP backbone (finance/HR/assets), AI seam (`platform.cyai` + `cyai_platform`), Ready-ERP provisioning, and audit — and adding the education domain plus four privacy-first GenAI capabilities.

---

## 0. Executive summary

- **Don't build from scratch.** CyED is a new product sibling to `cycom/` and `cymed/`, sharing the same `platform/` (tenant, audit, events, cyai, provisioning, terminology). ~50–60% of a real school system is billing, HR, assets, documents, and audit — **already built and test-green in CyCom** (81 backend tests passing).
- **Wedge:** no incumbent unifies SIS + LMS + finance + privacy-first AI + ACARA-native compliance in one ecosystem (parent / student / teacher / admin). Same "own the ecosystem" thesis proven in CyMed.
- **Compliance is the moat** (not a checkbox): the Australian Framework for Generative AI in Schools (6 principles / 25 guiding statements, endorsed June 2025), the new AU Framework for AI in Higher Education (Dec 2025), TEQSA integrity guidance, Privacy Act + AU data residency.
- **Deliver in phases**; each phase verified the way the 6 CyCom modules were (Django `check` + migrations + pytest + `tsc`).

---

## 1. World-best systems — research & what CyED takes

### K-12 Student Information Systems (SIS)
| System | Strength | Weakness | CyED takes / beats |
|---|---|---|---|
| **PowerSchool** | Most-deployed in North America; deep state reporting (all 50 US states); huge integration catalog | Heavy legacy UX, high admin burden, steep learning curve | Modern low-admin UX; keep the deep-reporting ambition |
| **Infinite Campus** | Strong mid/large districts; parent+student portals+app | Complex, US-centric | Portal/app parity from day 1 |
| **Alma** | Modern, clean UI; SIS+assessment+family engagement integrated | Smaller footprint | UX bar to match |
| **Veracross / Blackbaud** | Independent-school depth, advancement/fundraising | Expensive, niche | Reuse CyCom CRM/accounting for advancement |
| **Gradelink** | All-in-one for private/charter; billing+enrolment+support | SMB scale | Validates all-in-one + integrated billing (CyCom already has it) |

### Australia (the target market)
| System | Strength | Weakness | CyED implication |
|---|---|---|---|
| **Compass Education** | AU market leader; deepest integration ecosystem; parent app; acquiring adjacencies (Music Monitor 10/25, Inklass app 02/26) | Proprietary, integration-gated | Must match AU compliance + parent engagement, compete on open AI + price |
| **Sentral** | Broad AU government + independent footprint; wellbeing/pastoral depth | Dated in parts | Strong wellbeing/behaviour module needed to compete |
| **TASS / Edval** | TASS = admin+finance; Edval = best-in-class timetabling | Point solutions | CyED bundles finance (CyCom) + timetabling natively |

**AU non-negotiables (from research):** ACARA-aligned outcome tracking, NAPLAN/PAT context, state funding/reporting codes, **Australian hosting**.

### Higher-ed LMS (for the tertiary integrity capability)
| System | Strength | CyED implication |
|---|---|---|
| **Canvas (Instructure)** | Dominant HE share (> next 3 combined); UX + **open LTI** ecosystem | Be **LTI-interoperable**, don't reinvent the LMS wheel |
| **D2L Brightspace** | AI/adaptive (Lumi), outcomes-evidence for accreditation | Validates CyED's adaptive + **integrity-by-evidence** bets |
| **Moodle** | Open-source, full control | Option for institutions wanting self-host; interop target |
| **Blackboard** | Enterprise incumbency | Legacy displacement target |

**Insight:** incumbents are either SIS-deep (PowerSchool/Compass) *or* LMS-deep (Canvas) *or* finance-deep (TASS). **None unify all three + native, privacy-first AI.** That gap is CyED.

---

## 2. Scope — full school-management feature set

Legend: **NEW** = new `cyed` app · **REUSE** = existing CyCom app.

| Domain | Capability | Build |
|---|---|---|
| Admissions | Applications, offers, waitlist, enrolment | **NEW** `cyed.admissions` (+ REUSE `crm` pipeline) |
| SIS | Students, guardians, households, staff | **NEW** `cyed.sis` (+ REUSE `hr` for staff) |
| Academic structure | Year/term, subjects, **ACARA curriculum map**, class sections | **NEW** `cyed.academics` |
| Timetable | Rooms, periods, scheduling, clash detection | **NEW** `cyed.timetable` (+ REUSE `scheduler`, `inventory` rooms) |
| Attendance | Roll call, marks, absence workflows, SMS to parents | **NEW** `cyed.attendance` |
| Gradebook | Assessments, submissions, grades, moderation | **NEW** `cyed.gradebook` (+ REUSE `documents` for evidence/versioning) |
| Reporting | Report cards, achievement vs ACARA standards, NAPLAN/PAT context | **NEW** `cyed.reporting` |
| LMS | Courses, modules, lessons, content, LTI | **NEW** `cyed.lms` (+ REUSE `knowledge`, `documents`, `discuss`) |
| Wellbeing/behaviour | Pastoral notes, incidents, positive behaviour, medical/health | **NEW** `cyed.wellbeing` |
| Communication | Parent/student portals, notifications, newsletters | **NEW** portal + REUSE `marketing` (just built), notifications |
| Fees & billing | Fee schedules, invoicing, payment plans, statements | **REUSE** `accounting` + `ar_ap` (real, tested) |
| HR & payroll | Staff records, contracts, payroll, leave | **REUSE** `hr`, `payroll`, `leave` |
| Library | Catalog, loans, returns | **NEW** `cyed.library` (+ REUSE `inventory`) |
| Transport | Routes, buses, drivers | **REUSE** `fleet` |
| Facilities/assets | Rooms, equipment, maintenance | **REUSE** `inventory`, `maintenance` |
| Compliance | State reporting exports, audit, consent | **NEW** `cyed.compliance` + REUSE `platform.audit`, `access` |
| Analytics | Attendance/outcomes/finance dashboards | **NEW** + REUSE `cyai_reports` |

---

## 3. Architecture — how CyCom builds CyED

- **Repo shape:** new product `cyed/` sibling to `cycom/` and `cymed/`, importing shared `platform/`. This is exactly the cymed↔cycom split already in the repo. "Use CyCom to build CyED" = (a) share `platform/`, (b) copy CyCom's proven app pattern (`BaseModel` → serializer → `TenantScopedModelViewSet` → DRF router → `MODEL_ADAPTERS` frontend seam), (c) **reuse CyCom's finance/HR/asset apps directly** for the ERP half.
- **Stack (unchanged):** Django 6 + DRF + PostgreSQL RLS + Celery/Redis; Next.js frontend with the `useCycomList`/`MODEL_ADAPTERS` bridge; `platform.cyai` for AI; `platform.provisioning` for onboarding; **HITL queue** (already live at `/api/cycom/hitl/queue`) for human oversight.
- **Tenancy:** tenant = school; multi-campus districts modeled via facilities under one tenant. Row-level isolation via `BaseModel.tenant_id` (same as every CyCom app).
- **Curriculum as a terminology dataset:** ACARA content descriptions + achievement standards (coded, e.g. `AC9M8N01`) + state frameworks (NESA/VCAA) loaded into `platform.terminology`/registries — same mechanism CyMed uses for ICD/LOINC/SNOMED. This is what makes tutoring, lesson-gen, and reporting *curriculum-native*.
- **Reuse map:** accounting, ar_ap, hr, payroll, leave, fleet, inventory, maintenance, documents, access, audit, scheduler, discuss, marketing → plugged in, not rebuilt.

---

## 4. The four AI / EdTech capabilities (design)

All register as `AgentDefinition`s in `cyai_platform`, gated by `AgentEntitlement`, metered via `AgentUsageRecord`, with every human-review step routed through the existing **HITL queue**. Every call carries a `no_train` contract flag and tenant scoping.

### 4.1 Curriculum-Aligned Learning Assistants
- **RAG, not raw LLM.** Tutor answers *only* from retrieved ACARA/state-curriculum chunks, cited to the outcome code → no off-syllabus or hallucinated content.
- **Privacy-first as architecture:** `no_train=true` at the gateway; student inputs tenant-scoped, retention-windowed, never used for model training; AU data residency; per-interaction `AIInteractionLog` for transparency.
- Agent: `cyed.tutor`.

### 4.2 Automated Teacher Administrative Tools
- Generation agents `cyed.lesson_planner`, `cyed.rubric`, `cyed.differentiator` (tiered tasks), all grounded in the ACARA index so outputs map to curriculum codes.
- **Human-in-the-loop is the workflow, not a promise:** every generated artifact lands in the HITL queue for the teacher to edit/approve before use.

### 4.3 Academic Integrity & Authenticity Verification
- **Provenance, not a detector.** AI-text classifiers have unacceptable false-positive rates (the brief itself demands "without high false-positive rates") and are indefensible against a student — do **not** ship one as the core.
- **Design = process evidence:** draft/version lineage on submissions (`documents` versioning), writing-process analytics, an **AI-use disclosure** workflow, and oral/viva checkpoint scheduling. Signals route to HITL for a *human* decision — never auto-accuse.
- Aligns to TEQSA's process-based-assessment stance and the AU HE AI framework (Dec 2025). Target: tertiary (universities, TAFEs).

### 4.4 Adaptive & Special-Needs Education AI
- `LearnerProfile` entity: neurodivergence accommodations, **EAL/D proficiency level**, reading level, modality preferences.
- Adaptive engine selects next task from profile + mastery. EAL/D: on-the-fly readability leveling, first-language scaffolding, glossing. Neurodivergent: chunking, multimodal delivery, reduced-load layouts. Accommodations are data, applied consistently and auditable.

---

## 5. Privacy & compliance spine (Australia)

Maps to the **Australian Framework for Generative AI in Schools** — 6 principles: *Teaching & Learning, Human & Social Wellbeing, Transparency, Fairness, Accountability, Privacy & Security* (25 guiding statements) — plus the **AU Framework for AI in Higher Education** (Dec 2025) and **TEQSA** integrity guidance.

| Requirement | CyED mechanism |
|---|---|
| Privacy & Security | AU data residency; `no_train` gateway flag; retention + right-to-delete on student data; encryption |
| Transparency | `AIInteractionLog` + `platform.audit`; curriculum-cited AI outputs |
| Accountability | Every AI action attributable + reviewable via HITL |
| Human oversight | HITL queue mandatory on teacher-tools and integrity flags |
| Fairness | Bias review on adaptive engine; EAL/D + accessibility (WCAG) |
| Consent (minors) | Guardian/student consent records (reuse CyMed consent pattern) |

---

## 6. Key new data entities

`Student, Guardian, Household, Enrolment, AcademicYear, Term, Subject, CurriculumOutcome (ACARA), ClassSection, TimetableSlot, Room, RollCall, AttendanceMark, Assessment, Submission (+version lineage), Grade, ReportCard, Course, Module, Lesson, BehaviourIncident, WellbeingNote, LearnerProfile, ConsentRecord, AIInteractionLog` — staff/finance/assets reuse existing CyCom models.

---

## 7. Integrations

Curriculum (ACARA + state: NESA/VCAA), NAPLAN/PAT context, SSO (Google/Microsoft Education, state identity), **LTI** (Canvas/Moodle interop), AU payments (BPAY/Ezidebit/Stripe), messaging (SMS/email/push parent app), state MIS reporting exports.

---

## 8. Phased roadmap

| Phase | Deliverable | Verify gate |
|---|---|---|
| **0 — Foundation** | `cyed/` product scaffold sharing `platform/`; Education **Ready-ERP provisioning pack**; reuse-wiring to CyCom finance/HR | `check` + migrate |
| **1 — SIS core** | Students, guardians, enrolment, staff link, class sections | pytest + tsc |
| **2 — Academic** | ACARA curriculum import, timetable, attendance, gradebook, report cards | pytest + tsc |
| **3 — Engagement** | LMS + parent/student portals + fees (reuse accounting/ar_ap) | pytest + tsc |
| **4 — AI wave 1** | `cyed.tutor` (RAG) + teacher tools + HITL | eval + pytest |
| **5 — AI wave 2** | Integrity-by-provenance + adaptive/special-needs (EAL/D, neurodivergent) | eval + pytest |
| **6 — Compliance & pilot** | AU framework mapping, data-residency, consent, 1 pilot school | audit + pilot |

---

## 9. Risks

| Risk | Mitigation |
|---|---|
| AI-detection false positives | Provenance/evidence design, not a classifier; human decision via HITL |
| Student-data privacy (AU) | AU residency, `no_train`, retention/delete, consent, audit |
| ACARA/curriculum data licensing | Confirm ACARA data-use terms before ingestion |
| Incumbent lock-in (Compass/Sentral) | Compete on unified AI ecosystem + open interop (LTI/SSO) + price |
| Scope creep (K-12 + tertiary at once) | Phase it: K-12 SIS first; tertiary-integrity as a later, separable capability |

---

## 10. Recommended first slice (Phase 0 + start of 1)

Mirror the just-completed 6-module method: scaffold **`cyed` platform wiring + `cyed.sis` (Student / Guardian / Enrolment / ClassSection) + `cyed.gradebook` (Assessment / Grade)** as real Django apps (models/serializers/viewsets/urls/migrations/tests) + register **`cyed.tutor`** as an `AgentDefinition` stub in `cyai_platform` + an **Education provisioning pack** — all behind the same `check`/migrate/pytest/tsc gates. Proves the vertical end-to-end; ACARA RAG depth is Phase 4.
