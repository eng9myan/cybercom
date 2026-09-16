# CyED — Deployment Runbook

**For:** the person standing up CyED for a school or school group.
**Assumes:** PostgreSQL 14+, Python 3.12+, a TLS-terminating proxy.

Everything in Part 1 is enforced by `manage.py check --deploy`. If that command
passes, the things it covers are correct; if it fails, do not deploy. The check
exists because each failure it catches is **invisible at runtime** — the system
starts, serves traffic and passes its own test suite while silently not
protecting what it claims to.

---

## Part 1 — The database role (do this first)

CyED relies on PostgreSQL Row-Level Security as the database-level backstop for
tenant isolation: the thing that still holds when application scoping has a bug.

**A PostgreSQL superuser bypasses every RLS policy, `FORCE` included.** Django's
default `DB_USER` is `postgres`, which on a stock install is a superuser. A
deployment that takes the default creates all the policies, reports them as
enabled and forced, and gets no protection at all. Nothing observable
distinguishes that from a working system.

Create a role that owns nothing:

```sql
CREATE ROLE cyed_app LOGIN PASSWORD 'use-a-real-secret';
GRANT CONNECT ON DATABASE cyed TO cyed_app;
GRANT USAGE ON SCHEMA public TO cyed_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cyed_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cyed_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cyed_app;
```

Run **migrations** as the owner (they create tables and policies), then run the
**application** as `cyed_app`. Verify:

```sql
SELECT usesuper FROM pg_user WHERE usename = current_user;  -- must be false
```

`ATOMIC_REQUESTS` must stay enabled. The per-request tenant is published with
`SET LOCAL`, which only survives inside a transaction — without it the setting
is discarded and every policy falls through to its permissive "no tenant set"
branch. `check --deploy` enforces this (`cyed.E003`).

---

## Part 2 — Environment

| Variable | Required | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | yes | 50+ random characters. |
| `DJANGO_DEBUG` | — | Leave unset. `True` disables HTTPS redirect, HSTS and secure cookies. |
| `ALLOWED_HOSTS` | yes | Comma-separated. |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | yes | `DB_USER` must be the non-superuser role from Part 1. |
| `CYED_NOTIFY_SMS_ENABLED` | — | `1` to send SMS. |
| `CYED_NOTIFY_SMS_PROVIDER` | if SMS on | `twilio` or `console`. |
| `CYED_TWILIO_ACCOUNT_SID` / `_AUTH_TOKEN` / `CYED_TWILIO_FROM` | if Twilio | |
| `CYED_NOTIFY_EMAIL_ENABLED` | — | `1` to send email. |
| `CYED_NOTIFY_EMAIL_PROVIDER` | if email on | `smtp` or `console`. |
| `CYED_SMTP_HOST` / `_PORT` / `_USER` / `_PASSWORD` / `_FROM` / `_TLS` | if SMTP | Works with SendGrid, Mailgun, SES or a school relay. |
| `CYED_PAYMENT_PROVIDER` | — | Defaults to `manual` (offline BPAY/bank transfer). |
| `CYED_PAYMENT_WEBHOOK_SECRET` | if a gateway | |

**Enabling a channel without configuring its provider fails loudly rather than
dropping messages** (`cyed.E004`). That is deliberate: a school that believes it
has SMS and does not is worse off than one that knows it hasn't.

---

## Part 3 — Deploy sequence

```bash
python manage.py migrate                    # as the table owner
python manage.py check --deploy             # must pass; blocks on cyed.E001–E004
python manage.py collectstatic --no-input
```

Then start the app **as `cyed_app`**.

Post-deploy, confirm isolation is live:

```sql
SELECT relname, relrowsecurity, relforcerowsecurity
FROM pg_class WHERE relname LIKE 'cyed_%' AND relrowsecurity;
```

Every table listed in the governance RLS migrations must appear with both flags
true. `cyed.E002` checks this automatically, and the test suite fails if a model
holding personal data is added without a policy.

---

## Part 4 — First-year setup

1. **Provision the tenant and campuses** — one `Campus` per site.
2. **Load the curriculum**: `python manage.py import_mrac` (full ACARA v9 —
   2,764 content descriptions, 16,828 elaborations).
3. **Open the leave year**: `POST /api/v1/hr/leave-entitlements/open-year/`.
4. **Record staff clearances.** WWCC and teacher registration must be recorded
   *and verified* before anyone can be timetabled — this is enforced, not
   advisory, and a school that skips it will find it cannot assign classes.
5. **Set the library policy** and **sibling discount rules** if used.
6. **Import students, guardians and households**, then link families
   (`POST /api/v1/sis/families/{id}/members/`) so sibling pricing and
   consolidated statements work.

Optional but recommended before go-live:

```bash
python manage.py seed_academic_year --scale small --profile
```

on a scratch database, to see the reports and their query counts against real
volume.

---

## Part 5 — What is NOT closed by deploying this

Stated plainly, because these are the items an ST4S assessor or a procurement
panel will ask about, and none of them can be fixed in code.

| Item | Status | What is needed |
|---|---|---|
| **Card payments** | Not connected | A merchant account, then a provider subclass. Until then fees are recorded and reconciled offline (BPAY/bank transfer), which is how most Australian schools already take them. |
| **SIF AU certification** | Not certified | CyED implements the SIF AU v3.x data model and a stable RefId registry, and says so at `/api/v1/sif/coverage/`. It is **not** a certified Zone integration: no zone registration, no event publication, no consumer side. Give an assessor that endpoint's output, not a claim. |
| **MFA enforcement** | Code present, enforcement external | TOTP and backup codes exist. Enforcement belongs at the IdP; configure and evidence it there. |
| **Data sovereignty (APP 8)** | Deployment decision | Deploy to an Australian region (`ap-southeast-2` / Australia East) and keep backups in-region. Nothing in the code pins this. |
| **AI zero data retention** | Not evidenced | Student prompts are anonymised before any model call, but retention terms are contractual. Obtain enterprise ZDR terms or self-host the model. Until then, do not enable AI features on real student data. |
| **Penetration test** | Not done | Commission independently before a production go-live. |
| **Backups, monitoring, SSL certs** | Infrastructure | Out of scope for the application; verify them separately. |
| **LMS / accounting sync** | Not built | Canvas, Google Classroom, Xero and MYOB integrations do not exist. |

---

## Part 6 — Running the tests

Two backends, and both matter:

```bash
# Fast loop — SQLite, no services needed
DJANGO_SETTINGS_MODULE=core.settings_test python -m pytest -q

# The one that proves tenant isolation — RLS is a no-op on anything but Postgres
CYED_TEST_PG_URL=postgresql://user:pass@host:5432/postgres \
DJANGO_SETTINGS_MODULE=core.settings_test_pg python -m pytest -q
```

The SQLite run is faster and covers business logic. **It cannot tell you whether
tenant isolation works** — the RLS migrations return immediately on any
non-PostgreSQL backend, so the entire database-level backstop could be broken
and the suite would still be green. Run the PostgreSQL suite before any release.

Last full run: **920 passed on SQLite, 926 on PostgreSQL** (the six extra are
the RLS tests, which skip everywhere else).

---

## Part 7 — A local instance for demos and training

`START_DEV.bat` at the repo root runs the API on `:8095` against a SQLite file
with the dev-auth shim, which is what `cyed-web` proxies to by default:

```bash
START_DEV.bat migrate   # once — migrate + seed the demo tenant
START_DEV.bat           # then, to run it
```

Both flags the shim requires (`DJANGO_DEBUG`, `CYED_DEV_AUTH`) are set inside
that script and nowhere else. Production runs `core.settings`, which cannot
reach the bypass at all.

For a demo with something in it, seed a year of real volume and then fill the
modules around it:

```bash
python manage.py seed_academic_year --scale small --weeks 20
python manage.py seed_demo_content
```

The first gives 30 students across 24 classes with 3,600 attendance marks and
720 grades — enough that the leadership dashboard, the chronic-absence list and
the achievement spread all have something to show.

The second fills what that spine leaves empty: library loans (including one
overdue, so fines are exercised), admissions across every status, behaviour
incidents spread over twelve weeks, immunisation and health records, learner
profiles, staff leave and reviews, suppliers and purchase orders, inventory,
assets, transport subscriptions, visitors, draft report cards, relief teachers,
interview slots, exam candidates, messaging threads and payroll runs. It is
idempotent — re-running it adds nothing — and it stops short of anything that
posts to the general ledger, so the trial balance never disagrees with the
purchase history seeded beside it.

Without that second command an evaluator opening Library, Admissions or
Procurement sees "no records yet" and reasonably concludes the module was never
built.

### The four-school group demo

A second database holding a whole group, so the single-school instance stays
as it is:

```bash
START_DEV.bat group4
```

Build it (once) with:

```bash
set CYED_DEV_DB=D:\cybercom\CyEd\cyed_group4.sqlite3
python manage.py migrate
python manage.py seed_academic_year --campuses 4 --students-per-campus 220 --weeks 30
python manage.py seed_demo_content
```

That is 4 named NSW campuses, 880 students, 554 households, 48 staff, 96
classes, 158,400 attendance marks and 31,680 grades, plus every surrounding
module filled in proportion — 73 library loans, 598 behaviour incidents, 220
report cards, 44 NCCD records, 125 transport subscriptions.

**About 7% of students are seeded as poor attenders.** Giving every child the
same odds produced a population where nobody fell below 90%, so the
chronic-absence list — the cohort a school is actually accountable for — came
back empty and the leadership screen looked broken rather than clean. The tail
is chosen per student, not per mark, because a poor attender is a person with
a pattern; rolling it per mark averages back to the cohort mean.

Report timings at this volume (SQLite, 158k marks):

| Report | Time |
|---|---|
| Leadership dashboard (30 weeks) | ~3.3 s |
| Campus comparison | 0.6 s |
| At-risk analytics | 1.8 s |
| Census export (880 students) | 0.4 s |
| AR aging | 0.3 s |
| Trial balance | 0.2 s |

The dashboard is the one to watch: it is the slowest screen in the product and
the one an executive opens first. It is a scan over every attendance mark in
the window, so it will get slower as years accumulate. PostgreSQL with the
existing indexes is faster than SQLite here, but a group past ~10 campuses
should expect to pre-aggregate it.

### Testing as someone other than an admin

There is no Keycloak locally, so by default every visitor is a tenant admin —
which makes the parent and student portals show the whole school and hides
whether scoping works at all. Open **`/dev-identity`** and sign in as a
specific parent, student or teacher. That sets a cookie the API proxy turns
into a bearer token, so the real permission classes and the real student
scoping run.

Worth having an evaluator try, because these are enforced server-side and not
by hiding buttons:

| As a parent | Expected |
|---|---|
| `/api/v1/sis/students/` | only their own children |
| another family's child by id | 404 — not 403, so the id is not confirmed |
| `/api/v1/hr/staff/`, `/analytics/dashboard/`, `/health/sick-bay/current/` | 403 |

| As a student | Expected |
|---|---|
| own grades, attendance, timetable | 200 |
| `/api/v1/billing/families/`, `/billing/bills/` | 403 — fee arrears are not a child's business |

`/dev-identity` is development only: the proxy ignores the cookie in a
production build, and the production middleware verifies token signatures, so
an unsigned demo token is rejected outright.
