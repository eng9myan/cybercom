#!/usr/bin/env bash
# ============================================================
#  CyberCom Platform API (cymed) — Production Deploy
#  Run on the OCI VM by .github/workflows/deploy-backend.yml.
#
#  Docker Compose based, mirroring the proven pattern already running
#  the rest of the platform on this VM (/opt/cybercom-platform's
#  docker-compose.production.yml). Deploys to its own isolated stack
#  at /opt/cybercom-api (port 8011, own network/volumes) rather than
#  touching the existing /opt/cybercom-platform stack that already
#  serves api.cy-com.com on 8010 — cutting real traffic over is a
#  separate, explicitly-approved step once this is verified healthy.
#
#  Release layout (see deploy-backend.yml's bundle step):
#    release_dir/cymed/          — Django project (manage.py etc.)
#    release_dir/platform/       — shared package, sibling of cymed/
#    release_dir/infrastructure/ — Dockerfile.cymed + docker-compose.api.yml
# ============================================================
set -Eeuo pipefail

release="${1:?usage: deploy-production.sh <git-sha>}"
app_root="${APP_ROOT:-/opt/cybercom-api}"
release_dir="${RELEASE_DIR:-$app_root/releases/$release}"
shared_env="$app_root/shared/.env.production"
compose="docker compose --env-file $shared_env -f docker-compose.api.yml"
port="${APP_PORT:-8011}"

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

echo "==> Building image for release $release"
$compose build

echo "==> Starting database and cache"
$compose up -d postgres redis
echo "    Waiting for postgres to be ready..."
until $compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER"' >/dev/null 2>&1; do
  sleep 2
done

echo "==> Running database migrations"
$compose run --rm backend python manage.py migrate --noinput

echo "==> Collecting static files"
$compose run --rm backend python manage.py collectstatic --noinput --clear || true

echo "==> Starting all services"
$compose up -d

echo "==> Waiting for health check on port $port"
for attempt in {1..30}; do
  if curl --fail --silent --show-error "http://127.0.0.1:${port}/health" >/dev/null; then
    echo "Release $release is healthy and active on port $port"
    exit 0
  fi
  if [[ "$attempt" == 30 ]]; then
    echo "Health check failed for release $release" >&2
    echo "---- backend logs ----" >&2
    $compose logs --tail=100 backend >&2 || true
    exit 4
  fi
  sleep 2
done
