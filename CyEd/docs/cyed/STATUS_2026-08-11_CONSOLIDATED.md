# CyED — Consolidated Status (2026-08-11)

This merges the four prior audit docs (`DEPLOYMENT_READINESS_2026-08-09.md`,
`ACARA_DATA_AND_BLUEPRINT_GAP.md`, `AUDIT_WORKFLOWS_2026-08-11.md`,
`AUDIT_PROCUREMENT_AND_ST4S_2026-08-11.md`) plus a follow-up pass done this
session, into one current picture. Read the originals for full detail and
evidence; this is the synthesis, not a replacement.

## Verdict: NOT READY to deploy to production.

Ready for a controlled, no-real-PII pilot only, per the ST4S audit's
conditional-approval terms.

---

## 1. What changed in this session

- **Fixed:** the Tier-0 structural gap where `ClassSection`/`TimetableSlot`
  linked a teacher by free-text name only. Added real `teacher` FKs to
  `hr.Staff`, wrote backfill migrations (name-matched, ambiguous/unmatched
  cases reported rather than guessed), added `my-classes`/`my-timetable`
  endpoints, and fixed timetable conflict-detection to key off the FK instead
  of a name string (previously two staff sharing a name would collide, and
  differently-typed names for the same person wouldn't). Tests added in
  `sis/test_sis.py` and new `timetable/test_timetable.py`.
  **Caveat: could not run `manage.py makemigrations --check` or the test suite
  in this session** — see §4. Review the migrations and run the suite before
  merging.
- **Already fixed (verified, not by me):** the notification-delivery honesty
  bug (Finding 1 in the procurement/ST4S audit) — `delivery.py` and
  `test_delivery_honesty.py` were both written ~15 seconds after that audit
  doc was saved. Confirmed the fix is real: an enabled-but-unwired channel
  now returns `failed` with an honest error, never a false `sent`.
- **Resolved (as a documentation/decision issue, not a code issue):** the
  CyCom-proxy-vs-native-ERP contradiction. `products/cycom` does not exist in
  this repo; the native `hr`/`payroll`/`staff_attendance`/`accounting`/
  `inventory`/`procurement` apps are what's real and tested. `ERP_REUSE_CYCOM.md`
  is now marked superseded with an explicit ask: the product owner needs to say
  whether CyCom is a future product (keep the dormant proxy) or an abandoned
  plan (delete the doc and the `erp/` proxy app).

## 2. What's genuinely built and tested (unchanged from prior audits)

SIS, admissions, curriculum with the full ACARA v9 corpus loaded (per the
procurement audit — see §3 for a contradiction on this point), timetable with
conflict detection, attendance with guardian notification, gradebook with
report cards (tamper-evident, SHA-256), fees/billing/installments, transport
(most complete module — GPS, RFID, route optimisation), library, health,
events, visitors, LMS course structure, dual AI (teacher tools + Socratic
tutor, anonymised, human-in-the-loop), at-risk analytics, substitution engine,
RBAC + immutable audit + consent, multi-campus group layer, field encryption +
Postgres RLS, PWA + WCAG basics — and, as of Phase 0, native HR, Payroll,
Staff Attendance, Accounting, Procurement, Inventory, and Document Sign, with
proven cross-module links (payroll docks pay for an unexplained absence;
procurement receipt posts to the ledger and increments stock).

**357 backend tests passing** — suite re-run 2026-08-11 in a Python 3.12.13 venv
(`.venv/`), which supersedes the 174 figure from 2026-08-09.

## 3. Contradictions found across the audit docs

- **ACARA load size — RESOLVED 2026-08-11.** Counted directly against
  `cyed_dev.sqlite3`. The procurement/ST4S audit was right and
  `ACARA_DATA_AND_BLUEPRINT_GAP.md` is stale:

  ```
  outcomes                     19,592   (2,764 content descriptions + 16,828 elaborations)
  general_capabilities              7   (25,013 outcome links)
  cross_curriculum_priorities       3   ( 2,615 outcome links)
  achievement_standards            68
  mrac_import_runs                 17   (CC BY attribution stored per row)
  ```

  By learning area: Languages 12,245 · HASS 1,729 · Mathematics 1,289 ·
  The Arts 1,061 · Science 1,047 · English 1,029 · Technologies 660 · HPE 532.
  The stale doc is now banner-marked. **ACARA v9 coverage is proven.**
- **ST4S map vs ST4S audit — OPEN.** `docs/ST4S_COMPLIANCE_MAP.md` claims ZDR
  and AES-256 that the audit found absent, and understates the MFA code that
  does exist. Banner added there; the audit is authoritative. Reconcile before
  any assessor submission.
- **CyCom vs native ERP** — resolved, see §1.

## 4. What was NOT verified this session — do not treat as done

- ~~**No fresh test run.**~~ **RESOLVED 2026-08-11.** A Python 3.12.13 venv was
  built at `CyEd/.venv` and the suite run: **357 passed**. The teacher-FK
  migrations (`sis/0004`, `timetable/0002`) are applied and covered. One test
  failed on first run and was fixed — it asserted DRF's raw error dict where the
  project renders RFC 7807 problem+json; the conflict-detection behaviour itself
  was correct. Reproduce:

  ```
  DJANGO_SETTINGS_MODULE=core.settings_test DJANGO_SECRET_KEY=test-secret .venv/Scripts/python -m pytest -q
  ```

- **`payments` app has models but no migrations.** `PaymentIntent`, `Refund` and
  `WebhookEvent` exist in `payments/models.py` with indexes and constraints, but
  `makemigrations --check` reports them all as pending and the app exposes only
  2 routes. Written, never wired. Do not count it as a payment gateway.
- **`sif` app is an empty stub** (3-line `models.py`, 2 routes) — the SIF AU
  rejection blocker is untouched, not partially done.
- **No full-year data seed, no load test** — still the single highest-value
  next step per the prior audits: it would unblock the performance questions
  (several endpoints aggregate in Python, not SQL) and let the ACARA
  contradiction above be checked against real data.
- **No UI for the eight Phase-0 ERP modules** — still API-only.
- **No parent or student portal UI, no payment gateway** — still the two
  buyer-facing blockers flagged as CRITICAL in the procurement audit.
- **MFA, SIF AU, data-sovereignty evidence, AI ZDR terms** — still the four
  ST4S rejection blockers; none are code-only fixes.

## 5. Recommended next three actions, in order

1. Get this session's migrations and tests run and reviewed in a real
   Python 3.12+ environment — don't merge on the strength of code review alone.
2. Settle the ACARA load-size contradiction (§3) with a direct count query
   against the database.
3. Seed a full academic year and load-test — unblocks the most open questions
   at once (performance, data integrity, and a real ACARA re-check).

---

## Full backlog (everything flagged across all audits, for reference)

See `AUDIT_WORKFLOWS_2026-08-11.md` §7 (departmental fix plan, Tiers 0–5) and
`AUDIT_PROCUREMENT_AND_ST4S_2026-08-11.md` Section C (Tiers 1–4) for the
complete, prioritized lists — not duplicated here to avoid a third copy
drifting out of sync.
