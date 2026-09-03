# CyCom + platform runtime verification — 2026-09-04

CyCom is the **canonical core** (ADR-0001). This confirms it runs clean before the
consolidation builds on it.

## How it was run

- `cycom/.venv` (Python 3.12.13), `pip install -r requirements.txt`.
- `DJANGO_SETTINGS_MODULE=core.settings_test`, SQLite, `DEBUG=True`.

## Results

| Check | Result |
|---|---|
| `pip install -r requirements.txt` | clean, no missing deps |
| `manage.py check` | **0 issues** — all 39 `products/cycom/*` apps + `platform/*` load |
| `makemigrations --check --dry-run` | **No changes detected** — models ↔ migrations in sync |
| `pytest` | **103 passed, 0 failed** (8.7 s) |

**Conclusion:** the core is healthy. No blockers to starting Phase 0 on it.

## Coverage gap (known, not new)

- **26 test files across 39 apps.** 103 tests is thin for ~15k LOC.
- Strong where the buildout focused (catalog, POS, sales, accounting, CRM, payroll);
  little/none in the gap-fill apps (discuss, fleet, helpdesk, leave, marketing,
  planning, plm, project, recruitment) added in commit `7848b40`.
- `H` Q1 target: ≥ 80% overall, ≥ 95% finance/tax/payroll. Current is well below.
- **Phase-0/1 task:** raise coverage on the core transaction + finance paths before
  they carry migrated CyShop data; every gap-fill app needs at least a smoke test
  before it's exposed in a GA flavor.

## platform/ note

`platform/` is a shared app package with **no standalone Django project** — its 31
test files run inside a host project (cycom / cymed). `pytest platform/` from the
repo root fails with "no manage.py" — expected, not a bug. A dedicated
`platform/` test harness (its own minimal settings) is a Phase-0 nice-to-have so
the shared core can be tested in isolation in CI.

## Combined picture (both verification docs)

| Product | check | migrations | tests | verdict |
|---|---|---|---|---|
| **CyCom** (core) | clean | in sync | 103/103 | healthy; **coverage thin** |
| **CyMed** | clean | in sync | 486 pass / 23 fail / 6 err (~95%) | real; **~1wk hardening** (see `cymed-runtime-2026-09-04.md`) |

Both are genuine, working Django codebases. Neither is scaffold. The consolidation
starts from a real foundation.
