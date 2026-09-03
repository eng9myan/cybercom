# CyMed — Migrations Status

**Owner:** Platform team
**Version:** 1.0
**Date:** 2026-08-19
**Review cadence:** on every new-app landing

---

## Summary

- **Total `0001_initial.py`:** 115 across platform + products
- **Newly generated this hardening pass:** ~48 (P0-8 through P0-12 + MRFF-16..19 + payments/ai_cds/rcm)
- **Django `check`:** clean (0 issues)
- **SQLite dev migrate:** clean, all apps applied
- **PostgreSQL migrate:** not yet exercised — production DB requires PostgreSQL 16 + RLS bootstrap (see `platform/tenant/migrations` and `docs/adr/ADR-0002-multi-tenant-rls.md`)

## Issues resolved during this pass

| Fix | Where | Reason |
|---|---|---|
| `"core.patients.Patient"` → `"cymed_patients.Patient"` | `products/cymed/patient_portal/models.py:24` | Django app labels: `core.patients` app is `label=cymed_patients` |
| `"core.providers.Provider"` → `"cymed_providers.Provider"` | `products/cymed/provider_portal/models.py:10,76` | Same |
| `"patient_portal.PatientPortalProfile"` → `"cymed_patient_portal.PatientPortalProfile"` | `products/cymed/payments/models.py` (7 occurrences) | App label is `cymed_patient_portal` |
| `db_table = "cymed_clinic_referrals"` → `"cymed_clinic_referral_loop_referrals"` | `products/cymed/clinic/referral_loop/models.py:51` | Table-name collision with `cymed_clinic.referrals` |

## Regenerate command (single shot, all apps)

```bash
cd D:/cybercom/cymed
DJANGO_DEBUG=True DJANGO_SECRET_KEY=dev-unsafe \
  python manage.py makemigrations
```

## SQLite smoke test

```bash
cd D:/cybercom/cymed
DJANGO_DEBUG=True DJANGO_SECRET_KEY=dev-unsafe \
  python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
os.environ['DJANGO_DEBUG'] = 'True'
os.environ['DJANGO_SECRET_KEY'] = 'dev-unsafe'
from django.conf import settings
if not settings.configured: settings._setup()
settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'dev_smoke.db'}}
django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=1)
"
```

## PostgreSQL production migrate — checklist before running

- [ ] PostgreSQL 16 installed with `pg_stat_statements`, `uuid-ossp`, `pgcrypto`, `citext`
- [ ] RLS role bootstrap script executed (`docs/db/bootstrap_rls.sql`)
- [ ] Backup snapshot captured (RDS or pg_basebackup)
- [ ] `DATABASE_URL` env exported OR `DB_HOST/DB_NAME/DB_USER/DB_PASSWORD/DB_PORT` set
- [ ] `python manage.py check --deploy` clean
- [ ] Run `python manage.py migrate --plan` — review before applying
- [ ] Apply: `python manage.py migrate`
- [ ] Post-migrate: `python manage.py collectstatic --noinput`
- [ ] Post-migrate: create tenant + seed lookup data via `python manage.py loaddata seed/*.json`

## Known-issue notes

- **Referral naming split (P0-8):** two `Referral` models now exist — `clinic.referrals.Referral` (original) and `clinic.referral_loop.Referral` (closed-loop tracker). If you consolidate later, migration must include `AlterModelTable` + data copy + FK repoint.
- **`platform_api` migration 0001:** already applied in earlier session; retained.
- **UUID PK defaults from `platform.common.models.BaseModel`:** all newly created tables inherit `uuid.uuid4` default via `BaseModel.id`. This is safe under PostgreSQL and SQLite.
- **JSONField on SQLite:** works via `django.db.models.JSONField` (Django 4+ builtin). Postgres uses native `jsonb`.
