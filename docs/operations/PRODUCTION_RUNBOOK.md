# CyberCom Production Runbook

Status: operational reference for what's actually built. Not a full
production deployment guide — no environment has actually been deployed
by this work, everything below is derived from reading the real code,
not from operating a live system.

## Products and how to run each locally

All Django products (`cymed`, `cymart`, `cydrive`) share the same
bootstrap pattern:

```
cd <product>
DJANGO_DEBUG=True DB_NAME=<name> DB_USER=<user> DB_PASSWORD=<pw> python manage.py migrate
DJANGO_DEBUG=True DB_NAME=<name> DB_USER=<user> DB_PASSWORD=<pw> python manage.py runserver <port>
```

Ports used in cross-service config (`CYDRIVE_BASE_URL` in cymart's
settings): cymed convention implies 8000, cymart 8001, cydrive 8002 —
not enforced anywhere, just what the default settings assume; change
consistently if running multiple products together.

Run tests with `python run_tests.py` (not bare `pytest`) — the stdlib
`platform` module shadowing fix has to run before pytest loads, which a
conftest.py alone can't guarantee (see `platform/conftest.py`'s
docstring for why, discovered the hard way during Phase 1).

`cycom` is Odoo — `docker compose up -d` from `cycom/cycom-platform/`,
per that directory's own README.

`mobile` (React Native): `npm install`, `npx tsc --noEmit`, `npx eslint .
--ext .ts,.tsx --max-warnings 0`, `npx jest`. No `npm run android`/`ios`
verification possible from this environment — no simulator/device.

## Known-required environment variables

Every Django product needs `DJANGO_SECRET_KEY` when `DJANGO_DEBUG` isn't
`True`, plus `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` for a
real Postgres connection (tests use SQLite via `core.settings_test`
instead — no live DB needed for `python run_tests.py`).

`CYIDENTITY_ISSUER` / `CYIDENTITY_JWKS_URI` must point at a real Keycloak
instance for anything beyond the test suite's mocked JWKS — the 3
`cyidentity` integration tests that call out to a real Keycloak Admin
API are the only ones in the whole session that couldn't be made to pass
without one (documented since Phase 1, still true).

`CYDRIVE_BASE_URL` (cymart) must point at a running cydrive instance for
`OrderService.request_delivery()` to work outside of its mocked tests.

## Database migrations

Every product's migrations were only ever run against SQLite (via
`settings_test`) in this session — `manage.py makemigrations` was run
with dummy Postgres credentials that fail to connect (a harmless warning,
not a blocker, since `makemigrations` only needs model state). **Nobody
has run `manage.py migrate` against a real Postgres database in this
environment.** First real deployment needs to verify migrations apply
cleanly against actual Postgres, not just SQLite — SQLite is more
forgiving about some constraint/type edge cases.

## What's NOT covered here (real gaps, not oversights)

- **Rollback procedures** — not written. No deployment has happened to
  learn what actually needs rolling back.
- **Disaster recovery** — not written. No backup/restore process has been
  built or tested for any product's database.
- **On-premise deployment** — `platform.tenant`'s `TenantDeploymentProfile`
  model has the shape for dedicated-schema/dedicated-database/on-premise
  tiers, but no actual deployment tooling (Helm charts, Terraform, etc.)
  targeting those tiers exists in this repo.
- **Incident response** — not written.
- **Penetration testing / compliance sign-off (HIPAA, PCI-DSS)** — needs
  licensed specialists, genuinely out of scope for this work regardless
  of how much more code gets written. Flagging this explicitly rather
  than silently omitting it or pretending a code review substitutes for
  it.

## Verification approach used throughout this work (for whoever continues it)

Every commit in this session that touched Django code was verified with
`manage.py check` + the real test suite (via `run_tests.py`), not just a
code read. Every commit touching the mobile app was verified with
`npm install` + `tsc --noEmit` + `eslint` + `jest`. Cross-service
integrations (cymart↔cydrive) were verified by mocking the HTTP boundary,
same approach as the mobile app's API client tests. The one exception —
Odoo (`cycom`) — was verified by actually pulling the real `odoo:19`
Docker image and running the test suite against a throwaway Postgres
container, then tearing both down. Keep this bar; it caught real bugs
(wrong dependency names, broken jest config, browser-only APIs used in
React Native, a stale-directory read producing a wrong deletion, an
unreconciled tax field in settlement math) that a code read alone would
have missed every time.
