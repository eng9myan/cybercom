# CyED — Departmental Workflow Audit & Consolidated Fix Plan

**Date:** 2026-08-11
**Frame:** a 13-campus Australian school group running the system for a full
academic year of ordinary daily work.
**Method:** audited against the live API surface (all registered routes dumped
from the URL resolver) and the models behind them. Every gap below was verified
in code, not inferred.

---

## 0. The finding that reframes the rest

**`teacher_name` is free text. There is no link between a teacher and their work.**

```
sis/models.py:183        teacher_name = models.CharField(max_length=255, blank=True)
timetable/models.py:26   teacher_name = models.CharField(max_length=255, blank=True)
```

`hr.Staff` exists, with contracts, payroll, leave and attendance hanging off it.
`ClassSection` and `TimetableSlot` reference a teacher by *typed name*. Nothing
joins the two.

Consequences that surface immediately in daily use:

- A teacher cannot ask "what are my classes?" or "what is my timetable?" —
  there is no query that answers it. Every teacher-facing screen is therefore
  unbuildable without a workaround.
- The substitution engine matches on name strings, so "A. Nguyen" and
  "Anh Nguyen" are different people, and two staff sharing a surname collide.
- HR/payroll and teaching are separate universes: approving leave cannot know
  which classes need covering.
- A rename or typo silently orphans a teacher's entire load.

Everything in §1 depends on fixing this first. It is a data-model change, so it
should be scheduled ahead of the workflow features that need it.

---

## 1. Teacher workflow

| Step | Status | Detail |
|---|---|---|
| See my classes / timetable | **BROKEN** | No teacher↔class link (§0). No `my-classes` or `my-timetable` endpoint. |
| Take the morning roll | **PAINFUL** | Only `POST /attendance/marks/` one row at a time. A class of 30 = 30 requests, 30 `post_save` signals, 30 guardian-notification cycles inside the transaction. |
| Period-by-period attendance | PARTIAL | RollCall carries `period_label`, but no timetable-driven "next period to mark" flow. |
| Enter grades for an assessment | **PAINFUL** | `POST /gradebook/grades/` per student. Marking a set of 30 papers = 30 requests. |
| Mark submitted work | OK | `assessment/submissions/{id}/grade/` writes back to the gradebook. |
| Message a parent | **MISSING** | `notifications` is send-only from staff; there is no teacher↔parent thread, no reply path, no read receipt for a two-way conversation. |
| Create a lesson / assignment | OK | LMS + assessment cover it. |
| Generate report cards | PARTIAL | Publish is per-student. No "publish for this class" — a Year 7 teacher publishes 30 times. |
| Flag a struggling student | OK | Wellbeing + at-risk analytics. |

**Missing operational steps:** bulk roll marking, bulk grade entry, bulk report
publishing, a teacher's own landing view, and two-way parent messaging.

---

## 2. Student workflow

| Step | Status | Detail |
|---|---|---|
| View my timetable | **BROKEN** | `timetable/slots/` is unscoped CRUD; there is no "my timetable" and no student↔slot path. |
| Check my grades | PARTIAL | `gradebook/grades/` is student-scoped, but there is no assembled "my results" view. |
| Submit an assignment | OK | `assessment/assignments/mine/` + submission + `submit`. Verified working. |
| Sit a quiz | OK | Attempt/answer/submit with auto-marking. |
| View my attendance | PARTIAL | Marks are readable; no personal summary or rate. |
| Message a teacher | **MISSING** | No student↔teacher channel at all. |
| View fee status | N/A | Correctly a parent concern. |
| Student portal UI | **MISSING** | No `/portal/student` — all 31 frontend routes are staff-facing. |

---

## 3. Admissions workflow

| Step | Status | Detail |
|---|---|---|
| Application intake | OK | `admissions/applications/`. |
| Document checklist | **MISSING** | `intake` does OCR on uploads but is not bound to an application; no "birth certificate received" state. |
| Catchment / zone validation | **MISSING** | No catchment model or check at enrolment. |
| Interview / tour scheduling | **MISSING** | No workflow. |
| Offer | PARTIAL | Offer records exist; there is no parent-facing **accept/decline**, no expiry, no waitlist. |
| Enrol into SIS | OK | `applications/{id}/enrol/` creates the Student. |
| **Post-enrolment onboarding** | **MISSING** | `enrol` creates a bare Student. It does not attach the family, assign a fee plan, allocate a class, set up transport, or trigger consent forms. Every one of those is manual re-keying. |
| Mid-year transfer between campuses | **MISSING** | `Student.campus` is a bare FK with no transfer action or history (see the scale audit). |
| Withdrawal / exit | PARTIAL | Status can be set to `withdrawn`; no exit workflow, no Transfer Certificate, no final-fee settlement. |

**Assessment:** admissions can take an application and create a student, but the
*join-up* — the part a registrar actually spends their day on — is absent.

---

## 4. HR workflow

| Step | Status | Detail |
|---|---|---|
| Staff records / contracts | OK | Verified. |
| Onboarding / offboarding | OK | Idempotent checklists; offboard ends contracts and deactivates. |
| Leave request → approval | OK | Approval writes staff-attendance days. |
| **Leave balances** | **MISSING** | `StaffLeave` records days taken with **no entitlement, accrual or balance**. HR cannot answer "does she have leave left?" and cannot stop an over-draw. AU full-time staff accrue 4 weeks annual + 10 days personal — none of it is modelled. |
| **WWCC / clearance expiry** | **MISSING (compliance)** | No Working With Children Check number, no expiry date, no alerting. In Australia a school **must** verify and monitor WWCC validity; an expired clearance must block classroom contact. Nothing here tracks it. |
| Qualifications / registration | **MISSING** | No teacher-registration (VIT/NESA/TRB) number or renewal date. |
| Performance reviews | OK | Confidential, submit → acknowledge. |
| Position / payroll linkage | PARTIAL | Contract → payroll works; contract → *teaching load* does not (§0). |

---

## 5. Finance & payroll workflow

| Step | Status | Detail |
|---|---|---|
| Fee structure, invoices, installments | OK | |
| **Take a payment** | **MISSING** | No gateway. `payments` app is routed but has no endpoints. |
| **Sibling / family billing** | **MISSING** | `Family` exists and is inert — no discount rules, no consolidated statement. |
| Defaulter escalation | **MISSING** | Reminders exist; no staged ladder. |
| GL, P&L, balance sheet, budgets | OK | |
| Bank reconciliation | OK | Import, auto-match, exception report, finalise. |
| GST / BAS | OK | Derived from GL control accounts. |
| Debtor aging | OK | |
| Payroll run → payslips → paid | OK | Attendance-driven, reconcilable. |
| Credit notes / refunds | **MISSING** | No credit-note model. |

---

## 6. Other departments

**Library** — issue/return works; `overdue` is a status with **no fine
calculation, no overdue report, no borrower limits**.

**Health** — records and incidents exist, but **no immunisation register** (AU
enrolment requires immunisation status) and **no medication-administration log**
(a school administering prescribed medication must record each dose, who gave
it, and when — a duty-of-care record).

**Visitors** — sign in/out works; no pre-registration, no contractor induction
check, no evacuation roll.

**Transport** — the most complete module: zones, buses, subscriptions, GPS,
route optimisation, RFID boarding with guardian alerts.

**Wellbeing** — profiles, notes, check-ins, sentiment, at-risk. No merit/demerit
points on the existing behaviour records.

**Events** — events and participation exist; consent is not bound to the
docsign/consent-form flow.

---

## 7. Consolidated fix plan

Ordered so that each tier unblocks the next.

### Tier 0 — structural (everything else depends on these)
1. **Add `ClassSection.teacher` and `TimetableSlot.teacher` FKs to `hr.Staff`**, keep `teacher_name` as a denormalised fallback during migration. Backfill by name match, report unmatched.
2. **Apply campus scoping.** Wire the existing `scope_queryset_by_campus` into every tenant-scoped viewset carrying campus-bearing data.
3. **Student campus-transfer action + history model.**

### Tier 1 — safety, security, compliance
4. Move absence notifications out of the request transaction (queue).
5. MFA lockout: add an IP dimension; fix the backup-code PBKDF2 cost/timing.
6. **WWCC + teacher-registration fields with expiry alerting**, and block assignment when expired.
7. Immunisation register + medication-administration log.

### Tier 2 — daily-work throughput (the teacher's day)
8. **Bulk roll marking** — one request per roll call.
9. **Bulk grade entry** — one request per assessment.
10. `my-classes` / `my-timetable` / teacher landing (needs Tier 0 #1).
11. Bulk report-card publish per class.
12. Two-way teacher↔parent messaging.

### Tier 3 — performance at a year of 13-campus data
13. Move `trial_balance` / `_movements` aggregation into SQL.
14. Fix `auto_match` and `import_statement` N+1s.
15. Bound and index `ar_aging`, staff-attendance summary, org rollup.

### Tier 4 — money and admissions completeness
16. Payment gateway + finish the `payments` app surface.
17. Family/sibling discounts + consolidated statement.
18. Defaulter escalation ladder; credit notes.
19. Post-enrolment onboarding chain (family, fee plan, class, transport, consents).
20. Offer accept/decline, waitlist, catchment validation.

### Tier 5 — remaining departments
21. Leave entitlements/accrual/balances.
22. Library fines + overdue report; borrower limits.
23. Merit/demerit points; event consent bound to docsign.
24. Parent + student portals; SIF AU; exam operations; alumni/Transfer Certificates.

---

## 8. Honest summary

CyED's **record-keeping** is strong and its **back office is genuinely deep**
(double-entry GL, reconciliation, BAS, payroll driven by real attendance, ACARA
loaded in full, MFA, tenant isolation).

What it lacks is the **connective tissue of a school day**: the teacher is not
joined to their classes, the roll cannot be taken in one action, the registrar
must re-key everything an offer implies, and HR cannot answer either of the two
questions it is asked most — *how much leave is left* and *is this person's
clearance current*.

Those are not exotic features. They are the ordinary work.
