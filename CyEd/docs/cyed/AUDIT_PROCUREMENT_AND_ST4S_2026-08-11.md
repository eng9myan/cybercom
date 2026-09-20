# CyED — Procurement & Compliance Audit

**Date:** 2026-08-11
**Subject:** CyED School Management System / Education ERP
**Method:** Audited against the running codebase, not a specification. Every
status below was checked by reading source or exercising the API; claims I could
not verify are marked UNVERIFIED rather than assumed.

> **Declared conflict of interest.** This system was built in this same
> engagement. An author auditing their own work is structurally biased toward
> leniency, so the burden of proof here is inverted: a feature counts as present
> only if it is demonstrably wired end-to-end. "Model exists" is not "workflow
> works."

---

# SECTION A — School Operational Workflow Gap Analysis

## A.1 Workflow Status Matrix

| # | Workflow | Status | Evidence |
|---|---|---|---|
| 1 | **Admissions & SIS** | `PARTIALLY COMPLETE` | Application → offer → `enrol` creates a Student. Guardians, demographics, AU statutory fields, CSV bulk import, de-identification all present. **No catchment/zone validation. No sibling/family linkage for discounts.** |
| 2 | **Academic & Curriculum** | `VERIFIED COMPLETE` | Full ACARA v9 loaded (2,764 content descriptions, 16,828 elaborations, 7 capabilities, 3 CCPs, 68 achievement standards). Assessments carry ACARA codes; assignments/quizzes with auto-marking write back to the gradebook; report cards are tamper-evident (SHA-256) with per-school branding. |
| 3 | **Attendance & Absence** | `PARTIALLY COMPLETE` | Roll call, per-period marks, partial-day statuses, absence→guardian trigger on save. **Parent SMS/email is NOT actually sent (see A.3 Finding 1). No late-arrival pass printing.** |
| 4 | **Billing, Tuition & Finance** | `CRITICAL MISSING WORKFLOW` | Fee plans, installments, proration, late fees, overdue detection, reminders, double-entry GL, P&L, balance sheet, budgets, bank reconciliation — all real. **But there is no payment gateway: `method` is a text label. The system cannot take money.** No multi-child/sibling fee calculation. |
| 5 | **Staff Management & Timetabling** | `PARTIALLY COMPLETE` | Timetable with conflict detection; substitution engine proposes internal cover from free colleagues; leave request→approval writes staff-attendance days; payroll consumes attendance. **No external relief-teacher (CRT) booking — no CRT register, no availability, no offer/accept.** |
| 6 | **Parent & Student Portals** | `CRITICAL MISSING WORKFLOW` | Parent/student *data scoping* is implemented and tested (parents see only their children). **But there is no parent or student portal UI.** All 31 frontend routes are staff-facing. Parents cannot log in and see anything. |

## A.2 Missing Operational Features (day-to-day blockers)

**Blocking — a school cannot run without these:**

1. **Payment gateway.** Invoices, plans and balances compute correctly, but no
   card/BPAY/direct-debit integration exists. Fees must be reconciled by hand.
2. **Parent portal.** No UI for parents: no fee view, no payment, no permission
   slips, no report-card download, no attendance visibility.
3. **Student portal.** Students cannot view a timetable, submit work, or see
   grades through a UI — the assessment API supports it, nothing renders it.
4. **Real parent messaging.** See Finding 1 — the delivery path is a no-op.
5. **Sibling / family fee logic.** No family grouping, so no multi-child
   discount, no consolidated family invoice, no single family statement.

**Significant — schools will demand these at tender:**

6. Catchment/zone validation at enrolment.
7. CRT/relief-teacher register, availability and booking.
8. Late-arrival pass printing (and any physical print/kiosk path).
9. Fee defaulter escalation *workflow* (reminders exist; no staged escalation
   ladder, payment-plan negotiation, or debt-collection handoff).
10. Exam operations: hall tickets, seating allocation.
11. Student lifecycle tail: alumni archiving, Transfer Certificates.
12. Merit/demerit points (behaviour incidents exist without a points system).

## A.3 Named Findings

**Finding 1 — CRITICAL: notification delivery silently reports success.**
`products/cyed/notifications/delivery.py` marks a notification `sent` when the
channel is enabled, but performs **no provider call** — the integration point is
a comment. With `CYED_NOTIFY_SMS_ENABLED=1`, the system records SMS as delivered
while sending nothing.

This is worse than the un-configured state, which at least honestly reports
`queued`. In an attendance context it is a **duty-of-care risk**: the school
believes a parent was told their child is absent, and has a record saying so.

*Required fix:* the enabled branch must fail loudly until a real provider is
wired, and delivery status must reflect provider acknowledgement.

**Finding 2 — HIGH: no family/household entity.** Students link to Guardians
many-to-many, but there is no family unit. Sibling discounts, consolidated
invoices and family statements are all unimplementable without it. This is a
*data-model* gap, not a feature gap — it will require migration.

**Finding 3 — HIGH: parent-facing capability is API-only.** Parent scoping is
correctly implemented and adversarially tested, but is unreachable: no portal.
The capability is real; the product is not.

---

# SECTION B — Government & ST4S Verification Audit

## B.1 Compliance Matrix

| Standard | Requirement | Status | Evidence / Gap |
|---|---|---|---|
| **MRAC v9.0** | Native ingestion, JSON-LD/RDF, all learning areas | ✅ **COMPLIANT** | Ingests the real published MRAC from `vocabulary.curriculum.edu.au`; all 8 learning areas + 7 GCs + 3 CCPs loaded; ASN/SKOS parsed; elaborations linked to parents; capabilities linked via `asn:skillEmbodied`; CC BY 4.0 attribution stored per row. Regression-tested against verbatim ACARA fixtures. |
| **SIF AU v3.x** | SIF data model, 128-bit UUID RefIds, STATS/NAPLAN/NCCD reporting | ❌ **NON-COMPLIANT** | **Zero SIF implementation.** No RefIds, no SIF object mapping, no SIF/XML or zone interface. Primary keys are UUIDs but are *not* SIF RefIds and carry no SIF semantics. NCCD/NAPLAN/census exports exist as **bespoke CSV/JSON**, not SIF payloads — they are not machine-consumable by government endpoints. |
| **APP 8 — Data Sovereignty** | PII hosted onshore (AWS Sydney / Azure Melbourne) | ⚠️ **UNVERIFIED — deployment-dependent** | Nothing in the code pins a region; `docker-compose` runs anywhere. Sovereignty is entirely an infrastructure decision and **has not been demonstrated**. No documented data-residency control, no sub-processor register. |
| **APP (general)** | Consent, access, correction, erasure, breach response | 🟡 **PARTIAL** | Strong: consent records gate AI on a named student; immutable audit trail; data-portability export; de-identification endpoint. Missing: **no Notifiable Data Breach response plan**, no retention/disposal schedule, no privacy policy artefact. |
| **ST4S — TLS 1.3 in transit** | Enforced | ⚠️ **UNVERIFIED** | HSTS/secure cookies set in prod settings; actual TLS version is terminated at infrastructure not present here. |
| **ST4S — AES-256 at rest** | Enforced | 🟡 **PARTIAL** | Application-level **Fernet (AES-128-CBC + HMAC)** field encryption on health/wellbeing PII — this is *not* AES-256. Full-disk/database encryption is a deployment concern and unverified. |
| **ST4S — MFA for staff** | Enforced | ❌ **NON-COMPLIANT** | **No MFA anywhere.** No TOTP, no WebAuthn, no step-up auth. Auth validates RS256 JWTs from an external IdP; MFA would have to be enforced there and is not configured or evidenced. |
| **ST4S — RBAC data isolation** | Strict | ✅ **COMPLIANT** | Role sets + permission classes; per-tenant scoping on every queryset; object-level student scoping; **PostgreSQL Row-Level Security** with FORCE + tenant policy as a database backstop; `ATOMIC_REQUESTS` so the tenant GUC is request-scoped. Adversarially tested (15 attack tests) — no answer-key leakage, no cross-student reads, no cross-tenant reads. |
| **AI — Socratic guardrails** | No direct answers to students | ✅ **COMPLIANT** | Student-facing tutor returns guiding questions with `answer_withheld`; enforced in service and asserted by test. |
| **AI — Prompt anonymisation** | PII stripped pre-processing | ✅ **COMPLIANT** | `anonymize.py` strips names/emails/phones/IDs before any LLM call; wired into both tutor paths. |
| **AI — Zero Data Retention** | Enterprise ZDR terms | ❌ **NOT EVIDENCED** | The code notes retention is "handled at deployment/config". **No ZDR contract, no enterprise agreement, no configuration proving it.** Model calls go to a public API endpoint with a key. An auditor cannot accept an assertion here. |
| **AI — Human in the loop** | Teacher review of generated material | ✅ **COMPLIANT** | Every generated artefact lands in a review queue as `pending_review`; integrity decisions are always human; process-provenance (not text detection) avoids false-accusation risk. |

## B.2 Verification Verdict

> ## `REJECTED` — for ST4S badging and government interoperability
>
> ## `CONDITIONALLY APPROVED` — for a controlled single-school pilot, non-authoritative

**Rejection rests on four independent blockers, any one of which is sufficient:**

1. **No MFA for staff.** A hard ST4S control. Accounts reaching student PII are
   single-factor.
2. **No SIF AU v3.x.** The system cannot participate in government data exchange.
   Bespoke CSV is not interoperability.
3. **Data sovereignty unproven.** APP 8 requires demonstrated onshore hosting;
   nothing evidences it.
4. **ZDR not evidenced.** Student prompts reach an external model under
   unproven retention terms — even though they are anonymised first.

**Additionally disqualifying for production:** notification delivery reports
success without sending (Finding 1) — an auditor would treat a duty-of-care
channel that lies about delivery as a safety defect, not a bug.

**Conditional pilot** is defensible *only* with: no real student PII, or PII
under a signed onshore agreement; SMS/email disabled so no false delivery
records are created; MFA enforced at the IdP; and no reliance on the platform as
the authoritative record for statutory reporting.

---

# SECTION C — Prioritized Action Plan

Ordered by what unblocks the most, soonest.

### Tier 1 — Safety and honesty (do before any pilot)

1. **Fix notification delivery.** Make the enabled-but-unwired branch raise
   instead of marking `sent`. Status must come from provider acknowledgement.
2. **Integrate a real SMS/email provider** (Twilio/SendGrid or an AU provider)
   with delivery receipts, retries and a dead-letter queue.

### Tier 2 — Compliance blockers (required for badging)

3. **Enforce MFA for all staff** at the IdP; add step-up auth for finance,
   payroll, health and wellbeing routes. Evidence it in the SSP.
4. **Implement SIF AU v3.x**: add SIF RefIds alongside internal UUIDs, map
   StudentPersonal / StaffPersonal / SchoolInfo / StudentAttendance /
   StudentSchoolEnrollment, and emit SIF-conformant payloads for STATS, NAPLAN
   and NCCD.
5. **Pin and evidence onshore hosting** (AWS Sydney / Azure Melbourne):
   data-residency control, sub-processor register, region-locked storage.
6. **Obtain enterprise ZDR terms** for the model provider, or move inference to
   an onshore/self-hosted model. Until then, disable AI on real student data.
7. **Upgrade at-rest encryption to AES-256** (envelope encryption via KMS) and
   document full-disk/database encryption.
8. **Produce the governance pack**: System Security Plan, NDB-compliant Incident
   Response Plan, retention & disposal schedule, privacy policy, DPIA.
9. **Commission an independent penetration test** and an ST4S assessment.

### Tier 3 — Procurement blockers (schools will not buy without these)

10. **Payment gateway** with AU rails: card, BPAY, direct debit, payment plans,
    reconciliation back to the ledger.
11. **Parent portal**: children overview, attendance, grades, report cards,
    permission slips, fees and payment.
12. **Student portal**: timetable, assignments, submission, results.
13. **Family/household entity** + sibling discounts, consolidated invoices and
    family statements (data-model change — schedule the migration early).
14. **CRT/relief booking**: register, availability, offer/accept, cost tracking.
15. **Catchment/zone validation** at enrolment.
16. **Fee defaulter escalation ladder** with staged actions and audit.
17. **School-Home Learning Bridge.** Problem: inconsistency between school data,
    student progress, and home support, especially in underserved communities.
    A cross-school, parent-teacher portal synchronizing learning goals,
    assignments, attendance, and progress with family-facing insights and
    recommended at-home activities. Key features: cross-platform data sync
    (where allowed) showing learning targets/progress; culturally responsive
    micro-lessons and family resources; alerts for missed assignments or
    upcoming assessments; teacher-approved offline activity packs for
    low-connectivity areas. Must-have: elevates student outcomes and parental
    engagement across the country. Builds directly on the Parent Portal (#11)
    and Curriculum/gradebook data already in place — not a separate system.

### Tier 4 — Operational completeness

18. Late-arrival passes and print/kiosk paths.
19. Exam operations (hall tickets, seating).
20. Alumni archiving and Transfer Certificates.
21. Merit/demerit points on the existing behaviour records.
22. **Seed a full academic year and load-test** — the system has never run at
    realistic volume; several endpoints aggregate in Python rather than SQL and
    are unmeasured.

---

## Appendix — What is genuinely strong

Stated plainly, because an audit that only lists faults is not useful:

- **Curriculum**: the full published ACARA v9 corpus is loaded and correctly
  structured — not a sample, not hand-typed. Verified against source counts.
- **Tenant & role isolation**: defence in depth (app scoping + DB row-level
  security), and adversarially tested rather than assumed.
- **AI safety posture**: anonymise-before-inference, Socratic no-answer
  enforcement, consent gating, and human-in-the-loop review are all real and
  tested — this is stronger than most EdTech entrants.
- **Tamper-evident reporting**: report cards are content-hashed and verifiable.
- **Finance core**: genuine double-entry with balanced-posting enforcement,
  statements derived from the ledger rather than stored aggregates.
- **Segregation of duties**: self-approval of purchase requests is blocked.
