# CyED — Deployment Readiness Report

> ## ⚠️ PARTLY SUPERSEDED — 2026-08-11
>
> - **Test count.** "174 passing" is stale. Suite re-run on 2026-08-11 in a
>   Python 3.12.13 venv: **357 passed, 0 failed**. (One failure was found and
>   fixed on the day — a test asserting DRF's raw error shape where the project
>   renders RFC 7807 problem+json; the conflict-detection behaviour under test
>   was correct.)
> - **§6 "ACARA / curriculum compliance: NOT RE-VERIFIED"** is resolved. The
>   full MRAC v9 corpus is loaded — 19,592 outcomes (2,764 content descriptions
>   + 16,828 elaborations), 7 General Capabilities, 3 Cross-Curriculum
>   Priorities, 68 achievement standards. Counted against the database, not
>   claimed. The "~55 starter outcomes" figure is dead.
>
> Everything else in this report — no full-year seed, no load test, unprofiled
> Python-loop endpoints, missing UI, unverified ops (backups, monitoring, SSL) —
> **still stands**.

**Date:** 2026-08-09
**Scope run:** Phase 0 (build missing ERP modules) — complete and verified.
Phases 1–3 partially covered; see *What was NOT verified* before trusting any
"ready" claim.

**Verdict: NOT READY to deploy.** Phase 0 is genuinely done and tested, but the
system has never been exercised against a full year of data, no UI exists for
the modules built today, and several deployment-checklist items are unverifiable
from the codebase alone.

---

## 1. What was actually built and verified (Phase 0)

Baseline before this run: **147 backend tests**. After: **174 passing**, `manage.py
check` clean under both dev and production settings, all migrations applied.

Every item below was exercised through the real HTTP API with real auth
(RS256 JWT via the production middleware path), not by reading code.

### New modules

| Module | Status | Key evidence |
|---|---|---|
| **Staff Attendance** (`cyed_staff_attendance`) | Built | Self-service check-in/out, derived lateness + hours, timesheet roll-up with submit/approve, leadership-only summary |
| **Document Sign** (`cyed_docsign`) | Built | Draft → signatories → send (SHA-256 seal) → sign → completed, append-only audit trail, tamper detection |

### Extended modules

| Module | Was | Added |
|---|---|---|
| **HR** | Staff, Contract, StaffLeave | `PerformanceReview` (confidential, submit/acknowledge), `OnboardingTask` + onboarding/offboarding kickoff, leave approve/reject |
| **Payroll** | PayrollRun, Payslip | `SalaryComponent` (allowances/deductions), `PayslipLine` (itemised), payment history, **attendance-driven pay** |
| **Accounting** | Accounts, Journal, Trial balance | `Budget`/`BudgetLine` + variance, `BankStatementLine` + reconciliation, **P&L**, **balance sheet** |
| **Procurement** | Supplier, PO, POLine | `PurchaseRequest` + **2-level approval**, `GoodsReceipt` → **stock in + GL posting** |
| **Inventory** | Item, StockMove | `low-stock` alert feed, `by-category` register summary |
| **CYCOM ERP** | Proxy client | **Confirmed correct as-is** — see §5 |

### Cross-module links proven by test

- **Payroll ← Staff Attendance**: an unexplained absence docks pay. Verified:
  $96k salary → $8,000 base month; one absent day deducts $400 → gross
  **$7,600.00**. Allowances/deductions flow through to gross and withholding.
- **HR Leave → Staff Attendance**: approving leave writes those weekdays as
  *paid leave*, so payroll never mistakes them for absence.
- **Payroll ↔ Attendance reconciliation**: `runs/<id>/reconcile/` detects drift
  when attendance changes after processing (verified in both directions).
- **Procurement → Inventory → Accounting**: PR → finance approval → leadership
  approval → PO → goods receipt increments `on_hand` **and** posts a balanced
  Dr Inventory / Cr Accounts Payable journal entry.

---

## 2. Bugs found and fixed during this run

| # | Severity | Bug | Fix |
|---|---|---|---|
| 1 | **High** | **Segregation-of-duties hole**: a finance user could approve their own purchase request. Confirmed by probe — returned `200 approved`. | `SelfApprovalError` in `decide_request`; now `403`. Rejecting your own request is still allowed (legitimate withdrawal). Regression test added. |
| 2 | **High** | `PurchaseOrder.receive` was a **stub** — flipped `status` to `"received"` with no body, no stock movement, no ledger posting. Goods "received" that never existed. | Replaced with real `receive_goods()`: per-line quantities, over-receipt rejection, partial receipts, stock moves, GL posting. |
| 3 | **Medium** | `read_only_fields = fields` where `fields = "__all__"` assigns a *string*; DRF raises `TypeError` the first time the serializer builds fields. **5 serializers affected, one pre-existing** (`compliance.StatutoryReportLogSerializer` — latent, never hit by a test). | Added `core.serializers.ReadOnlyModelSerializer`; all 5 converted. |
| 4 | **Medium** | Stale `prefetch_related` cache: after receiving the final quantity, the PO stayed `partially_received` because `po.lines.all()` returned the viewset's prefetched (pre-update) rows. | Query `PurchaseOrderLine` directly when rolling status forward. |
| 5 | Low | Model related-name collision: `docsign.SignableDocument.student` clashed with `intake.DocumentIntake.student` (both `Student.documents`). Blocked `manage.py check`. | Renamed to `signable_documents`. |

---

## 3. Permissions verified

Each of these is asserted by a passing test, not assumed:

- Teacher **cannot** read payroll runs or payslips (403).
- Teacher **cannot** read P&L, balance sheet, or budgets (403).
- Teacher sees **only their own** staff-attendance rows; leadership sees all.
- Attendance **summary** is leadership-only (403 for teacher).
- Teacher **cannot** approve their own timesheet (403).
- Teacher **cannot** author a performance review (403); cannot read another
  staff member's review (filtered to zero rows).
- Only the reviewed staff member may **acknowledge** their review.
- Offboarding is leadership-only (403 for teacher).
- Finance **cannot** give level-2 (leadership) approval on a purchase request.
- Parents see **only documents they are a signatory on**; cannot author documents.
- A non-signatory **cannot** sign a document.

## 4. Invalid-input / edge cases verified

Double check-in; check-out before check-in; check-in with no linked Staff record
(clear 400, not a 500); approving an unsubmitted timesheet; paying an unprocessed
payroll run; deciding a leave request twice; completing an already-complete task;
submitting an empty purchase request; over-receipt against a PO; receiving
against a *draft* PO; converting a rejected request; unbalanced journal entry;
reconciling a bank line twice; signing without a typed name; signing twice;
signing a **tampered** document (409).

## 5. CYCOM ERP module — scope confirmed, not a stub

`products/cyed/erp/` is a **deliberate proxy**, not an unfinished module. It
forwards whitelisted paths to CyCom's ERP with the caller's token, is staff-only,
and returns `503` when `CYED_CYCOM_URL` is unset. Since CyED now runs its own
native HR/payroll/finance/procurement/inventory/assets, this proxy is *optional*
by design (documented in `ERP_REUSE_CYCOM.md`).

**Recommendation:** confirm with the product owner whether "CYCOM ERP module"
in the brief means this proxy. If it is meant to be a distinct feature set, the
scope is undefined and cannot be built without a spec — flagging rather than
guessing.

---

## 6. What was NOT verified — do not treat as ready

These are the honest gaps. Nothing below has been exercised.

### Phase 1 — full-year seeding: **NOT DONE**
No seed of an Aug–Jun academic year was generated. Everything above was proven
on purpose-built fixtures (single staff member, small POs), **not realistic
volume**. Consequently:
- **Performance under a full year of data: UNKNOWN.** No query profiling was
  done. `Timesheet.recalculate()`, `budget_vs_actual`, `balance_sheet`, and the
  attendance `summary` endpoint all iterate in Python rather than aggregating in
  SQL — these are the likely first bottlenecks and **need load testing**.
- Data-integrity checks for orphaned records / broken relationships across a
  year of data: **not run**.

### Phase 2 — role simulation: **PARTIAL**
Exercised via API: HR Manager, Payroll Officer, Accountant (ERP),
Procurement/Inventory Officer, general Staff member.
**Not exercised:** Admin/Principal, Teacher, Student, Parent, Accountant/Finance
(student fees), Librarian, Receptionist, IT Admin — and **no** end-to-end run
through the UI for any role.

### Frontend: **MISSING for everything built today**
Staff Attendance, Document Sign, performance reviews, onboarding, budgets, bank
reconciliation, purchase requests, and goods receipts have **API only — no UI**.
The nav has no entries for them. Mobile/responsive behaviour for these modules is
therefore **unverified**.

### ACARA / curriculum compliance: **NOT RE-VERIFIED THIS RUN**
The `compliance` app exists with NCCD, attendance, NAPLAN and census exports, and
`curriculum` holds an ACARA registry (~55 starter outcomes). But this run did
**not** confirm: every subject mapped to a learning area; A–E achievement
standards on *every* report card; NAPLAN bands attached to the right Year
3/5/7/9 students. **The full licensed ACARA dataset is still not loaded** — only
the starter set. Treat ACARA compliance as **unproven**.

### Deployment checklist: **mostly unverifiable from code**
| Item | Status |
|---|---|
| Migrations run cleanly | ✅ Verified (dev + prod settings, `check` clean) |
| Environment variables documented | ✅ `.env.example` + `DEPLOYMENT.md` exist |
| Field encryption / DB RLS | ✅ Code present and tested |
| Backups configured | ❌ **Not verified** — infrastructure |
| Error monitoring / logging | ❌ **Not verified** — no Sentry/APM wired |
| SSL / domain | ❌ **Not verified** — infrastructure |
| Browser compatibility | ❌ **Not tested** |
| Mobile responsiveness | ⚠️ Verified previously for existing pages only |

---

## 7. Blocking issues before deploy

1. **Build UI for the eight new/extended ERP areas** — API-only modules cannot be
   used by the staff who need them.
2. **Seed and test a full academic year**, then profile the Python-loop endpoints
   listed above.
3. **Prove ACARA compliance** with the licensed dataset — currently unproven.
4. **Run the remaining eight roles** end-to-end, through the UI.
5. **Stand up ops**: backups, error monitoring, SSL — none verified.
6. **Confirm CYCOM ERP scope** with the product owner.

## 8. Recommended next step

Phase 1 (seed a full year) is the highest-value next move: it unblocks the
performance, data-integrity, and ACARA checks simultaneously, and gives the
remaining role simulations something realistic to run against.

---

## Reproduce

```bash
cd D:/cybercom/CyEd
DJANGO_SETTINGS_MODULE=core.settings_test DJANGO_SECRET_KEY=test-secret python -m pytest -q
# 174 passed
```
