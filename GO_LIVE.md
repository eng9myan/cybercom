# GO_LIVE.md — CyCom production deployment (first paying customer)

Turnkey sequence to take CyCom live, tying together the existing composes + the
Keycloak prod stack. This is the last mile after the Phase 2 build. It runs on
**your** host — the steps are exact; the values in **CAPS** are yours to fill.

Assets referenced (all already in the repo):
- `infrastructure/docker-compose.cycom-api.yml` — Postgres + Redis + Django backend (gunicorn) + Celery.
- `infrastructure/docker-compose.keycloak-prod.yml` + `keycloak/README-prod.md` — auth.
- `infrastructure/Dockerfile.cycom` — backend image (python 3.12, gunicorn).
- `cycom/cycom-erp` — Next.js frontend (`next build` / `next start`).

## What I need from you to finish (the only blockers)
1. **A host** (Linux VM with Docker) + **two DNS records**: `app.YOURDOMAIN`, `auth.YOURDOMAIN`.
2. **A TLS reverse proxy** (Caddy/nginx/Traefik) on the host.
3. **Secrets** (you set them; I never handle them): DB passwords, Keycloak admin + client secret, `DJANGO_SECRET_KEY`.
4. **Payment provider decision**: launch on `manual` (bank transfer) now, or provide Stripe/HyperPay/PayTabs keys.
5. **Confirm the 2 payroll rates** flagged in PROJECT_STATE (SA scheme, UAE national %).

## Sequence

### 1. Keycloak (P0)
Follow `infrastructure/keycloak/README-prod.md` fully:
```bash
cd infrastructure
cp .env.keycloak.example .env.keycloak    # fill KC_HOSTNAME=auth.YOURDOMAIN + secrets
docker compose -f docker-compose.keycloak-prod.yml --env-file .env.keycloak up -d
```
Then set the `cybercom-backend` client secret (README step 5) and note it.

### 2. Backend app env
Create `infrastructure/.env.cycom-api` (never commit) with at least:
```
DJANGO_SETTINGS_MODULE=core.settings
DJANGO_SECRET_KEY=LONG-RANDOM
DJANGO_DEBUG=False
# DB / cache
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
# Auth — point at prod Keycloak, and DISABLE the dev shim
CYIDENTITY_ISSUER=https://auth.YOURDOMAIN/realms/cybercom
CYIDENTITY_JWKS_URI=https://auth.YOURDOMAIN/realms/cybercom/protocol/openid-connect/certs
KEYCLOAK_TOKEN_URL=https://auth.YOURDOMAIN/realms/cybercom/protocol/openid-connect/token
KEYCLOAK_CLIENT_ID=cybercom-backend
KEYCLOAK_CLIENT_SECRET=...          # from step 1
CYCOM_DEV_AUTH=0                     # MUST be off in prod (else dev_auth bypass loads)
# Payments (P0)
CYCOM_PAYMENT_PROVIDER=manual        # or "stripe" + the STRIPE_* keys below
# STRIPE_SECRET_KEY=... STRIPE_PUBLISHABLE_KEY=... STRIPE_WEBHOOK_SECRET=...
```

### 3. Bring up backend + workers
```bash
docker compose -f infrastructure/docker-compose.cycom-api.yml --env-file infrastructure/.env.cycom-api up -d --build
# one-time, inside the backend container:
docker compose -f infrastructure/docker-compose.cycom-api.yml exec backend python manage.py migrate
docker compose -f infrastructure/docker-compose.cycom-api.yml exec backend python manage.py collectstatic --noinput
docker compose -f infrastructure/docker-compose.cycom-api.yml exec backend python manage.py seed_packs
docker compose -f infrastructure/docker-compose.cycom-api.yml exec backend python manage.py bootstrap_platform_realm --admin-email you@YOURDOMAIN --admin-username platformadmin
```

### 4. Frontend
Build + run with prod env (point it at the backend + itself):
```
CYCOM_BACKEND_URL=http://backend:8000            # or the internal backend URL
NEXT_PUBLIC_APP_URL=https://app.YOURDOMAIN
CYCOM_DEV_AUTH=0
CYCOM_TENANT_ID=                                 # leave empty in prod (real login, not dev tenant)
```
```bash
cd cycom/cycom-erp && npm ci && npm run build && npm run start   # or containerize behind the proxy
```

### 5. Reverse proxy (Caddy example)
```
auth.YOURDOMAIN { reverse_proxy 127.0.0.1:8080 }   # Keycloak
app.YOURDOMAIN  { reverse_proxy 127.0.0.1:3000 }   # Next.js frontend
# backend stays internal; the frontend proxies to it server-side.
```

## Go-live verification checklist
- [ ] `https://auth.YOURDOMAIN/realms/cybercom` loads (realm imported).
- [ ] `POST https://app.YOURDOMAIN/api/cycom/signup/register` → 201 with a real `realm_name` (no `IdentityRealm.DoesNotExist`).
- [ ] `/signup` shows the payment step (bank instructions for `manual`, or gateway redirect).
- [ ] Pay (bank confirm → finance marks invoice paid, or gateway webhook) → tenant flips **active**.
- [ ] Log in as the new tenant admin (real Keycloak, not dev-login).
- [ ] Provision a Commerce tenant via `/setup`; POS rings a sale; `/kds` shows the ticket.
- [ ] `CYCOM_DEV_AUTH` is **0** everywhere (grep the running env).

## After first customer (not launch blockers)
Item 3 hosting/provisioning platform (multi-tenant instance automation), full Arabic i18n, accounting report polish, CRM UI. See PROJECT_STATE.md.
