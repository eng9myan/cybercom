# CyED — Deployment Guide

CyED is a **standalone** system (its own full ERP; CyCom reuse is optional). This
guide takes it from the verified dev build to a production pilot.

## Stack
- **API** — Django 6 + gunicorn (WSGI), PostgreSQL 16, Redis, WhiteNoise static.
- **Web** — Next.js 16 (server-rendered proxy → API).
- **Identity** — CyIdentity/Keycloak (OIDC), shared realm.

## Quick start (Docker, one command)
From the **repo root** (`D:/cybercom`), so the shared `platform/` + `shared/` are in context:

```bash
cp CyEd/.env.example CyEd/.env      # then edit CyEd/.env (set DJANGO_SECRET_KEY!)
docker compose -f CyEd/docker-compose.yml --env-file CyEd/.env up --build
```

- API → http://localhost:8000  · Web → http://localhost:3000
- The API container runs `migrate` on boot. Seed a demo school:
  `docker compose -f CyEd/docker-compose.yml exec api python manage.py seed_cyed_demo`
- Load the full ACARA v9 export (licensed CSV/JSON):
  `... exec api python manage.py import_curriculum --tenant <uuid> --file /path/acara_v9.csv`

## Manual (no Docker)
```bash
cd CyEd
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=core.settings DJANGO_SECRET_KEY=... DB_HOST=... ALLOWED_HOSTS=...
python manage.py migrate && python manage.py collectstatic --noinput
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
# web:
cd cyed-web && npm ci && npm run build && CYED_BACKEND_URL=http://localhost:8000 npm run start
```

## Production hardening checklist (ST4S / Australian Privacy Principles)
| Item | How |
|---|---|
| **AU data residency** | Deploy DB + app in AWS ap-southeast-2 (Sydney) or Azure Australia East. |
| **Secrets** | `DJANGO_SECRET_KEY` + DB creds from a secrets manager, never in the image. |
| **TLS 1.3** | Terminate at the ingress (Kong/NGINX/ALB); HSTS is already on when `DJANGO_DEBUG=False`. |
| **MFA / SSO** | Point `CYIDENTITY_ISSUER` at your Keycloak realm; enforce MFA there. The auth middleware already validates RS256 JWTs via JWKS. |
| **DB row-level security** | Application-layer tenant scoping is enforced today; add Postgres RLS policies keyed on `app.current_tenant_id` (the middleware already sets the GUC) for defence-in-depth. |
| **Field-level encryption** | Wrap sensitive columns (health/wellbeing) with pgcrypto or an app-layer Fernet field + KMS-managed key. |
| **Encryption at rest** | Enable KMS volume encryption on the DB + object store. |
| **Backups onshore** | Automated encrypted snapshots in the same AU region (APP 8). |
| **Audit/SIEM** | `AuditEvent` (immutable) + ship logs to an AU-hosted SIEM. |
| **Accessibility** | Run a WCAG 2.1 AA pass on `cyed-web` before go-live. |
| **Pen test** | Third-party test + zero criticals before handling real student data. |

## Verified build state
- Backend: **129/129 tests pass**, `check` clean, no pending migrations.
- Frontend: `tsc` + `next build` clean.
- Env-gated seams (LLM/OCR/STT/SMS/WhatsApp/payments/CyCom) fail safe when unset.
