# CyMed runtime verification — 2026-09-04

Closes the open question in `M_risk_register.md` R05 ("CyMed runtime unverified —
~68k LOC, never run this cycle"). Verdict: **substantially real, not scaffold;
needs a focused hardening pass before HealthFlavour can pilot.**

## How it was run

- No system Python on the dev box → built `cymed/.venv` (Python 3.12.13) from
  `pip install -r requirements.txt -r requirements-dev.txt`.
- `DJANGO_SETTINGS_MODULE=core.settings_test`, SQLite, `DJANGO_DEBUG=True`.
- `manage.py check` · `makemigrations --check` · `migrate --run-syncdb` · `pytest`.

## Results

| Check | Result |
|---|---|
| `manage.py check` | **0 issues** — all ~16 CyMed apps + gap-fill apps + `platform/*` load and wire URLs |
| `makemigrations --check` | **No changes detected** — models match committed migrations |
| `migrate` (SQLite) | **all migrations apply clean** |
| `pytest` (full suite) | **486 passed · 23 failed · 6 errors** (~95% green), 36 s |

**Conclusion:** this is a genuine, working Django codebase with real models,
services, serializers, URL wiring, and a large passing test suite — not a
skeleton. The `[core+]` primitives the blueprint assigns to Phase 3 (Ward,
Admission, OperatingSession, etc.) already have implementations here to port.

## Bugs found

| Severity | Bug | Fix |
|---|---|---|
| **Low (real)** | `requests` is imported by `integrations/hakeem/client.py` and `integrations/zakata/client.py` but was **not in `requirements.txt`** — a fresh install can't import those URLconfs (`manage.py check` fails) | added `requests>=2.31.0,<3.0.0` to `requirements.txt` (this commit) |
| Info | `datetime.datetime.utcnow()` in `integrations/hakeem/hl7_builder.py` — deprecated, removed in a future Python | Phase-1 cleanup |
| Info | bare `select_related()` (no args) in `laboratory/orders/views.py`, `imaging/orders/views.py`, `pharmacy/*/views.py` — `RemovedInDjango70Warning` | Phase-1 cleanup (Django 7 blocker) |

## Hardening pass (same day) — 486/23/6 → **510 pass / 5 fail / 0 err**

| Fix | Files | Effect |
|---|---|---|
| `settings_test`: `CELERY_TASK_ALWAYS_EAGER` + memory broker/backend | `core/settings_test.py` | model `post_save` → `task.delay()` no longer stalls the suite on a ~20-retry Redis reconnect storm (220 s → 26 s) |
| `settings_test`: `PLATFORM_RATE_LIMIT_ENABLED = False` | `core/settings_test.py` | **13 hospital tests** — passed solo, 429'd in the suite (60 req/min/IP `platform.security` middleware). Now pass. |
| `pay_bill` / `check_eligibility` / `submit_preauth`: pass `tenant_id` from the loaded parent (`bill`/`policy`) | `payments/services.py` | 3 real tenant-scoping bugs — `BaseModel` rows created with no `tenant_id` → `IntegrityError`. |
| `pay_bill`: settle against `patient_due`, and don't double-count the just-created txn | `payments/services.py` | real logic bug — a half payment was marked `paid` (added `charge_amount` on top of a `prior` sum that already included it; also compared to `total` incl. insurance). |
| rcm scrubber tests: build a fresh `SimpleNamespace` **subclass** per claim | `rcm/tests/test_scrubber.py` | 6 errors + 2 fails — `type(claim).objects = ...` can't set attrs on immutable `SimpleNamespace`; a subclass is mutable. All 38 rcm tests pass. |

### Remaining: 5 nphies tests — blocked on tenant-context infrastructure
`NphiesInteraction` (a `BaseModel`, tenant-scoped) is created inside the NPHIES client,
which has **no tenant awareness** — the client methods take `provider_tenant_id` as a
free string (NPHIES provider licensee), not the platform tenant UUID. Correct fix =
the `TenantScopedManager` + `tenant_context` ContextVar from
`specs/canonical-data-model-v1.md` §2.2 (auto-inject `tenant_id` on `.create()` from
request/task context). Lands with that implementation in Phase 1; a hack here would
mask the design gap. Tracked in `M` R05.

## Original failure triage (for reference)

| Cluster | Count | Representative | Likely cause | Owner |
|---|---|---|---|---|
| **payments** — `test_services_pay_bill.py` | 4 | `IntegrityError: NOT NULL constraint failed: cymed_payment_transactions.tenant_id` | the pay-bill service/factory doesn't set `tenant_id`; tenant is not injected from context. **Directly relevant to the consolidation** — tenant scoping must be consistent. | Health + Platform |
| **rcm** — `test_scrubber.py` | 6 errors + 2 fail | setup error before assertions; `test_duplicate_claim_rule` / `test_policy_expired_rule` fail | claim-scrubber test fixtures broken or a rule regression | Health |
| **nphies** — `test_coverage_eligibility_request.py`, `test_preauth_and_claim.py` | 5 | FHIR bundle assertions (`use` = preauthorization/claim; bundle shape) | FHIR R4 bundle builder drift vs test expectations; or a mocked-HTTP fixture issue | Health |
| **hospital** — `test_hospital.py::TestHospitalEdition` | 13 | whole class fails in the full run; `test_bed_management_operations` **passes in isolation** | **test isolation / shared-state**, not a code bug — a fixture leaks between the hospital suite and something earlier | Health (QA) |

None of the 23 is a "the feature doesn't exist" failure. The pattern is
integration-test fixtures + one real tenant-scoping gap in payments.

## Impact on the plan

- **R05 downgraded**: CyMed is real. HealthFlavour's Phase-2/3 timeline stands.
- **New Phase-1 task**: "CyMed test-suite hardening" — ~1 week: fix the payments
  `tenant_id` gap (real), repair the rcm/nphies fixtures, isolate the hospital
  suite, clear the Django-7 deprecations. Gate before HealthFlavour pilot.
- The payments `tenant_id` finding feeds `M` R03 (tenant isolation) — audit every
  CyMed model's `tenant_id` nullability + whether services inject it, as part of
  the M4 re-home.
- `requirements.txt` now installs clean — added to the migration M4 checklist.

## Repro

```bash
cd cymed
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt -r requirements-dev.txt
DJANGO_SECRET_KEY=x DJANGO_SETTINGS_MODULE=core.settings_test .venv/Scripts/python -m pytest -q
```
