#!/usr/bin/env bash
# ============================================================
#  Cycom ERP API — Production Deploy
#  Run on the OCI VM by .github/workflows/deploy-cycom-backend.yml.
#
#  Docker Compose based, mirroring cymed's proven pattern (same VM,
#  same deploy discipline). Deploys to its own isolated stack at
#  /opt/cycom-api (port 8012, own Postgres/Redis) - reuses the shared
#  Keycloak already running as part of cymed's stack via an external
#  Docker network reference, rather than duplicating it.
#
#  Release layout (see deploy-cycom-backend.yml's bundle step):
#    release_dir/cycom/         — Django project (manage.py etc.)
#    release_dir/platform/      — shared package, sibling of cycom/
#    release_dir/shared/        — shared package, sibling of cycom/
#    release_dir/infrastructure/ — Dockerfile.cycom
#    release_dir/docker-compose.cycom-api.yml
# ============================================================
set -Eeuo pipefail

release="${1:?usage: deploy-production.sh <git-sha>}"
app_root="${APP_ROOT:-/opt/cycom-api}"
release_dir="${RELEASE_DIR:-$app_root/releases/$release}"
shared_env="$app_root/shared/.env.production"
compose="docker compose --env-file $shared_env -f docker-compose.cycom-api.yml"
port="${APP_PORT:-8012}"

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

# See cymed's deploy-production.sh for the full story on why this
# symlink is required: each service's own "env_file: .env.production"
# directive in the compose YAML resolves relative to the compose
# file's own directory, completely separately from the --env-file CLI
# flag above (which only affects ${VAR} substitution inside the YAML
# itself). Without this, Compose fails to load the project at all.
ln -sfn "$shared_env" "$app_root/current/.env.production"

echo "==> Building image for release $release"
$compose build

echo "==> Starting database and cache"
$compose up -d postgres redis
echo "    Waiting for postgres to be ready..."
pg_ready=0
for attempt in $(seq 1 60); do
  if $compose exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER"' >/dev/null 2>&1; then
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
  $compose logs --tail=100 postgres >&2 || true
  exit 5
fi

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
