# CyEd — Data Retention & Disposal Schedule

**Status: DRAFT.** The windows below are defaults implemented in `products/cyed/governance/retention.py`, not a legal determination for any specific jurisdiction. A school must confirm its own statutory record-keeping obligations (state education department policy, APP 11.2's "no longer needed" test) and adjust `RETENTION_POLICIES` accordingly before treating these numbers as authoritative.

## 1. Mechanism

`python manage.py run_retention_sweep` (dry-run by default; `--apply` to act, `--tenant <uuid>` to scope to one school) sweeps for records past their window and either de-identifies or purges them. Every action is logged to `AuditEvent` (actor `system:retention_sweep`) — nothing is ever silently deleted, and the dry-run mode reports exactly what *would* happen before anything acts. This command is not currently scheduled anywhere; an operator must add it to a cron/CronJob for the sweep to actually run on a cadence.

## 2. Current schedule

| Category | Default window | Action | Rationale |
|---|---|---|---|
| Students | 7 years after `exit_date` (graduated or withdrawn) | De-identify (name, email, student number, DOB stripped; anonymised academic/statistical record preserved) | Balances a school's legitimate need for historical/statistical continuity against APP 11.2 — adjust to your state's actual minor-record retention requirement, which commonly runs to the student's 25th birthday in some Australian jurisdictions and may be longer than 7 years from exit |
| Visitor sign-in logs | 365 days | Hard delete | Operational/security record, not a long-term one |
| Admissions applications | 2 years after creation, **only** for terminal unsuccessful outcomes (`declined`, `withdrawn`) | Hard delete | An application that never became an enrolment has no ongoing purpose once its own outcome is old. Open/waitlisted applications are never touched by this sweep |
| Enrolled/active students | — | Never touched | The sweep only ever matches `graduated`/`withdrawn` status with a set `exit_date` |
| Financial records (invoices, payroll, GL) | Not yet in the automated sweep | — | Financial retention typically runs 5-7 years under tax/audit law and is commonly longer than the operational windows above — an operator should extend `retention.py` with a finance-specific sweep before relying on this schedule for financial-record compliance |
| Health/wellbeing records | Not yet in the automated sweep | — | Health-record retention for minors is often the longest category in AU jurisdictions (commonly to age 25 or later) — deliberately left to manual/legal review rather than an automated default that could be wrong in the direction of premature disposal |

## 3. What the sweep does NOT do (by design)

- It never deletes a student who is still `enrolled`, regardless of age.
- It never re-identifies a record once de-identified (the operation is irreversible, matching the existing manual `StudentViewSet.deidentify` endpoint it reuses).
- It never acts across tenants — `--tenant` scoping and the underlying queries are always `tenant_id`-filtered.

## 4. Extending the schedule

To add a new category, add an entry to `RETENTION_POLICIES` in `products/cyed/governance/retention.py` and a corresponding `sweep_<category>()` function following the existing pattern (query → dry-run report → `AuditEvent` on apply). Do not bypass the dry-run-by-default convention — it is the safety mechanism that makes an automated deletion schedule trustworthy.

## 5. Review

Owner: ______________________. Last technical accuracy check: 2026-09-20 (matches `retention.py` as committed).
