#!/usr/bin/env bash
# ============================================================
#  CyShop — Production Deploy
#  Run on the OCI VM by .github/workflows/deploy-cyshop.yml.
#
#  Docker Compose based, mirroring the release-directory pattern used by
#  cymed/scripts/deploy-production.sh and cycom's equivalent. Deploys to
#  its own isolated stack at /opt/cyshop (ports 8020/3020) — the same
#  ports/layout cyshop's own docker-compose.yml and the live nginx config
#  (website/nginx/cy-com.com.conf) already expect for cyshop.cy-com.com.
#
#  IMPORTANT — network name compatibility:
#  infrastructure/docker-compose.api.yml (cymed's stack) already joins an
#  EXTERNAL network literally named "cyshop_default" for cross-product
#  demo-provisioning calls. cyshop's own docker-compose.yml declares no
#  explicit networks section, so Compose creates one implicit default
#  network named "<project>_default". Project name is pinned explicitly
#  below with `-p cyshop` (NOT left to be inferred from the release
#  directory's basename, which changes every deploy) specifically so
#  that implicit network always resolves to "cyshop_default" and cymed's
#  existing external reference keeps working across every future deploy.
#
#  Release layout (see deploy-cyshop.yml's bundle step):
#    release_dir/backend/           — Django project (manage.py etc.)
#    release_dir/frontend/          — Next.js app
#    release_dir/docker-compose.yml — references ./backend, ./frontend
#  This mirrors the exact relative layout already inside cyshop/ in the
#  repo, so docker-compose.yml's build.context values work unmodified.
# ============================================================
set -Eeuo pipefail

release="${1:?usage: deploy-production.sh <git-sha>}"
app_root="${APP_ROOT:-/opt/cyshop}"
release_dir="${RELEASE_DIR:-$app_root/releases/$release}"
shared_env="$app_root/shared/.env.production"
compose="docker compose -p cyshop --env-file $shared_env -f docker-compose.yml"
backend_port="${BACKEND_PORT:-8020}"
frontend_port="${FRONTEND_PORT:-3020}"

if [[ ! "$release" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "Invalid release identifier: $release" >&2
  exit 2
fi

if [[ ! -r "$shared_env" ]]; then
  echo "Missing production environment file: $shared_env" >&2
  exit 3
fi

ln -sfn "$release_dir" "$app_root/current"
cd "$app_root/current"

# cyshop-backend's Dockerfile bakes DB_PASSWORD/DJANGO_SECRET_KEY etc. in
# at runtime via docker-compose.yml's `environment:` block (not env_file:),
# which is resolved by Compose from ${VAR} substitution using --env-file —
# so the flag above is sufficient here, no extra per-service symlink
# needed (unlike cymed's separate env_file: directive on each service).

echo "==> Building images for release $release"
$compose build

echo "==> Starting database and cache"
$compose up -d postgres-db redis-cache
echo "    Waiting for postgres to be ready..."
pg_ready=0
for attempt in $(seq 1 60); do
  if $compose exec -T postgres-db sh -c 'pg_isready -U "${DB_USER:-cyshop_admin}" -d "${DB_NAME:-cyshop_db}"' >/dev/null 2>&1; then
    echo "    postgres ready after ${attempt} attempt(s)"
    pg_ready=1
    break
  fi
  echo "    ...still waiting (attempt ${attempt}/60)"
  sleep 2
done
if [[ "$pg_ready" != 1 ]]; then
  echo "postgres never became ready" >&2
  echo "---- postgres logs ----" >&2
  $compose logs --tail=100 postgres-db >&2 || true
  exit 5
fi

# cyshop-backend's own entrypoint.sh already waits for postgres, runs
# `migrate --noinput` and `collectstatic --noinput` on every container
# start before handing off to gunicorn — no separate migrate/collectstatic
# step needed here, unlike cymed's script where that's done explicitly.
echo "==> Starting all services"
$compose up -d

echo "==> Waiting for backend health check on port $backend_port"
healthy=0
for attempt in {1..30}; do
  if curl --fail --silent --show-error "http://127.0.0.1:${backend_port}/healthz/" >/dev/null; then
    echo "Backend for release $release is healthy on port $backend_port"
    healthy=1
    break
  fi
  if [[ "$attempt" == 30 ]]; then
    echo "Backend health check failed for release $release" >&2
    echo "---- backend logs ----" >&2
    $compose logs --tail=100 cyshop-backend >&2 || true
    exit 4
  fi
  sleep 2
done

echo "==> Waiting for frontend on port $frontend_port"
frontend_up=0
for attempt in {1..30}; do
  if curl --fail --silent --show-error "http://127.0.0.1:${frontend_port}/" >/dev/null; then
    echo "Frontend for release $release is responding on port $frontend_port"
    frontend_up=1
    break
  fi
  if [[ "$attempt" == 30 ]]; then
    echo "Frontend health check failed for release $release" >&2
    echo "---- frontend logs ----" >&2
    $compose logs --tail=100 cyshop-frontend >&2 || true
    exit 6
  fi
  sleep 2
done

# Idempotent — get_or_create everywhere (see seed_demo.py). Safe to run on
# every deploy. This is what makes the homepage's "Launch Live Demo"
# button (-> /login?demo=1) actually work: without this, that button
# hits real login credentials that don't exist yet.
if [[ "$healthy" == 1 && "$frontend_up" == 1 ]]; then
  echo "==> Seeding demo tenant + owner demo login"
  $compose exec -T cyshop-backend python manage.py seed_demo
fi
