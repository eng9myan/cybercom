# CyShop Commerce OS

Multi-tenant enterprise commerce platform.

- **Backend:** Django 6 + DRF + GraphQL (Graphene) + Channels, JWT auth, multi-tenant middleware. PostgreSQL 15, Redis 7.
- **Frontend:** Next.js 14 (App Router) + Tailwind v4 in `frontend/`.
- **Marketing/Legacy SPA:** Vite + React 19 at the repo root (deployed via AWS Amplify, see `amplify.yml`).

> Note: the repo currently ships **two** frontends. The Dockerized stack uses the Next.js app in `frontend/`. The root-level Vite SPA is an alternate marketing build for Amplify and is not wired into docker-compose.

## Quick start (Docker, production stack on `cyshop.cy-com.com`)

```bash
cp .env.example .env
# edit .env — at minimum set DJANGO_SECRET_KEY and DB_PASSWORD
docker compose up --build -d
```

The bundled **Caddy reverse proxy** serves everything on one domain with
automatic Let's Encrypt TLS. Path-based routing:

| Path                      | Routed to               |
|---------------------------|-------------------------|
| `/api/*`, `/admin*`, `/graphql*`, `/healthz*`, `/static/*` | `cyshop-backend` (Django + Gunicorn) |
| Everything else           | `cyshop-frontend` (Next.js) |

Endpoints once DNS resolves:

- App: <https://cyshop.cy-com.com/>
- API: <https://cyshop.cy-com.com/api/v1/>
- Swagger: <https://cyshop.cy-com.com/api/schema/swagger-ui/>
- GraphQL: <https://cyshop.cy-com.com/graphql/>
- Health: <https://cyshop.cy-com.com/healthz/>

### DNS

Point an **A record** for `cyshop` under the `cy-com.com` zone at the host's
public IP. Ports `80` and `443` (TCP + UDP) must be reachable from the
internet so Caddy can complete the ACME challenge and serve HTTP/3.

```
cyshop.cy-com.com.   A   <your-host-public-ip>
```

For local testing without DNS, hit `http://<host>:80/` — the bare-IP block
in `Caddyfile` proxies the same routes without TLS.

The backend container waits for Postgres, runs migrations, collects static, then launches Gunicorn.

## Local dev (no Docker)

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DJANGO_DEBUG=True USE_SQLITE=True
python manage.py migrate
python manage.py runserver
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

## Production checklist

1. Generate a strong `DJANGO_SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(64))"`).
2. Set `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to your real domain(s).
3. Set `DJANGO_CORS_ALLOWED_ORIGINS` to the exact frontend origin(s) — do **not** rely on the dev-mode wildcard.
4. Put the stack behind a TLS-terminating reverse proxy (the backend honors `X-Forwarded-Proto`).
5. Rotate `DB_PASSWORD` and store it in a secret manager (not committed to git).
6. Point `NEXT_PUBLIC_API_URL` at the public backend URL.

## CI

GitHub Actions in `.github/workflows/ci.yml` runs:
- Django `check` + tests (SQLite)
- Next.js production build
- Docker image build for both services

## Repo layout

```
backend/                Django project (core_project + apps/*)
frontend/               Next.js 14 app
src/, public/, index.html, vite.config.js   Vite SPA (Amplify build)
amplify.yml             AWS Amplify build spec (targets the Vite SPA)
docker-compose.yml      Full stack: postgres + redis + backend + frontend
```
